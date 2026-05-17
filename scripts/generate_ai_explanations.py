"""Gemini로 공인중개사 1차 기출 JSON에 aiExplanation 해설을 생성·저장.

사용 예시:
  python scripts/generate_ai_explanations.py --input assets/jsons
  python scripts/generate_ai_explanations.py --input assets/jsons/2005-05-22.json
  python scripts/generate_ai_explanations.py --input assets/jsons --missing-only --batch-size 3
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from exam_image_urls import exam_choice_image_url, exam_question_image_url

REPO_ROOT = Path(__file__).resolve().parent.parent
IMAGE_PROBE_TIMEOUT_SECONDS = 8.0
DEFAULT_JSON_DIR = REPO_ROOT / "assets" / "jsons"
SESSION_MANIFEST_NAME = "exam-sessions.json"

MODEL_NAME = "gemini-flash-lite-latest"
CACHE_MIN_TOKEN_COUNT = 1024
STUCK_TIMEOUT_SECONDS = 30
MAX_RETRIES = 5
DEBUG_LOG_DIR = REPO_ROOT / "logs" / "ai_response_debug"
DEFAULT_VERTEX_LOCATION = "global"
AUTO_RESTART_ON_STUCK = True
MAX_AUTO_RESTARTS = 20
RESTART_DELAY_SECONDS = 3

SYSTEM_INSTRUCTION = (
    "당신은 공인중개사 1차 시험(부동산학개론, 민법 및 민사특별법) 전문 강사입니다. "
    "수험생이 빠르게 정답을 찾을 수 있도록 '쪽집게 해설'을 제공합니다. "
    "불필요한 설명 없이 핵심 개념, 정답 근거, 오답 비교를 명확하게 설명합니다. "
    "'옳은 것은?' 문제에서는 정답 보기가 왜 맞는지, "
    "'틀린 것은?'·'적절하지 않은 것' 문제에서는 오답·부적절 보기가 왜 틀렸는지 정확히 짚습니다."
)


class StuckTimeoutError(RuntimeError):
    """모델 호출이 비정상적으로 오래 걸릴 때 강제 종료하기 위한 예외."""


def _is_retryable_error(error: Exception) -> bool:
    message = str(error).lower()
    retryable_tokens = (
        "429",
        "rate limit",
        "resource_exhausted",
        "quota",
        "temporarily unavailable",
        "deadline exceeded",
        "503",
        "500",
        "timeout",
        "timed out",
    )
    return any(token in message for token in retryable_tokens)


def _response_text(resp: Any) -> str:
    """non-text 파트가 포함된 응답에서도 텍스트 파트만 안전하게 추출한다."""
    text_parts: list[str] = []
    for candidate in getattr(resp, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            text = getattr(part, "text", None)
            if text:
                text_parts.append(text)
    if text_parts:
        return "".join(text_parts).strip()
    text = getattr(resp, "text", None)
    return (text or "").strip()


def _generate_with_timeout_and_retry(
    client: genai.Client,
    *,
    contents: str | list[Any],
    config: types.GenerateContentConfig,
    batch_label: str,
) -> Any:
    for attempt in range(1, MAX_RETRIES + 1):
        start = time.perf_counter()
        executor = ThreadPoolExecutor(max_workers=1)
        timed_out = False
        try:
            future = executor.submit(
                client.models.generate_content,
                model=MODEL_NAME,
                contents=contents,
                config=config,
            )
            return future.result(timeout=STUCK_TIMEOUT_SECONDS)
        except FuturesTimeoutError as e:
            elapsed = time.perf_counter() - start
            timed_out = True
            future.cancel()
            message = (
                f"{batch_label} 응답 대기 {elapsed:.1f}s 초과 "
                f"(기준 {STUCK_TIMEOUT_SECONDS}s): 스턱으로 판단해 종료합니다."
            )
            raise StuckTimeoutError(message) from e
        except Exception as e:
            if (not _is_retryable_error(e)) or attempt == MAX_RETRIES:
                raise
            backoff = min(30.0, (2 ** (attempt - 1)) + random.uniform(0.0, 1.0))
            print(
                f"  - 재시도 {attempt}/{MAX_RETRIES} ({batch_label}) "
                f"error={type(e).__name__}: {e} | {backoff:.1f}s 후 재시도"
            )
            time.sleep(backoff)
        finally:
            if timed_out:
                executor.shutdown(wait=False, cancel_futures=True)
            else:
                executor.shutdown(wait=True)
    raise RuntimeError(f"{batch_label} 재시도 루프가 비정상 종료되었습니다.")


def _read_dotenv_value(env_path: Path, key: str) -> str | None:
    if not env_path.exists():
        return None
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() != key:
            continue
        value = v.strip().strip('"').strip("'")
        return value or None
    return None


def _load_api_key() -> str:
    """우선순위: 환경변수 > 프로젝트 .env > web/.env"""
    env_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key

    for env_path in (Path.cwd() / ".env", REPO_ROOT / ".env", REPO_ROOT / "web" / ".env"):
        key = _read_dotenv_value(env_path, "GOOGLE_API_KEY") or _read_dotenv_value(
            env_path, "GEMINI_API_KEY"
        )
        if key:
            return key

    raise RuntimeError(
        "API 키를 찾을 수 없습니다. 저장소 루트 .env에 GEMINI_API_KEY(또는 GOOGLE_API_KEY)를 "
        "설정하세요. (Google AI Studio 키는 AIza... 또는 AQ. 로 시작할 수 있습니다.)"
    )


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _build_genai_client() -> tuple[genai.Client, str]:
    """환경변수 설정에 따라 Gemini Developer API 또는 Vertex AI 클라이언트를 생성한다."""
    use_vertex = _env_flag("GOOGLE_GENAI_USE_VERTEXAI", default=False)
    if use_vertex:
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise RuntimeError(
                "GOOGLE_GENAI_USE_VERTEXAI=1 인 경우 GOOGLE_CLOUD_PROJECT가 필요합니다."
            )
        client = genai.Client(
            vertexai=True,
            project=project,
            location=DEFAULT_VERTEX_LOCATION,
        )
        return client, f"vertexai(project={project}, location={DEFAULT_VERTEX_LOCATION})"

    api_key = _load_api_key()
    client = genai.Client(api_key=api_key)
    return client, "developer-api(api_key)"


def _remote_image_exists(url: str) -> bool:
    """웹 ExamOptionalRemoteImage과 같이 시도; 없으면(404 등) False."""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method)
            req.add_header("User-Agent", "joonggaego-generate-ai-explanations/1.0")
            if method == "GET":
                req.add_header("Range", "bytes=0-0")
            with urllib.request.urlopen(req, timeout=IMAGE_PROBE_TIMEOUT_SECONDS) as resp:
                return resp.status in (200, 206)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            continue
        except (urllib.error.URLError, TimeoutError, OSError):
            continue
    return False


def _image_exists_cached(url: str, cache: dict[str, bool]) -> bool:
    if url not in cache:
        cache[url] = _remote_image_exists(url)
    return cache[url]


def _item_payload(
    item: dict[str, Any],
    *,
    image_probe_cache: dict[str, bool],
) -> dict[str, Any]:
    """문항·보기 이미지는 원격에 있을 때만 URL 필드를 넣는다(없으면 생략)."""
    question_id = str(item.get("id", ""))
    choices_raw = item.get("choices", [])
    choices_out: list[dict[str, Any]] = []
    if isinstance(choices_raw, list):
        for ch in choices_raw:
            if not isinstance(ch, dict):
                continue
            no = ch.get("no")
            try:
                choice_no = int(no)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
            choice_entry: dict[str, Any] = {
                "no": choice_no,
                "text": ch.get("text"),
            }
            choice_url = exam_choice_image_url(question_id, choice_no)
            if _image_exists_cached(choice_url, image_probe_cache):
                choice_entry["image_url"] = choice_url
            choices_out.append(choice_entry)

    payload: dict[str, Any] = {
        "id": question_id,
        "exam_type": item.get("exam_type"),
        "exam_session": item.get("exam_session"),
        "subject": item.get("subject"),
        "question_number": item.get("question_number"),
        "question_text": item.get("question_text"),
        "choices": choices_out,
        "correct_answer": item.get("correct_answer"),
        "choice_count": len(choices_out),
    }
    question_url = exam_question_image_url(question_id)
    if _image_exists_cached(question_url, image_probe_cache):
        payload["question_image_url"] = question_url
    return payload


def _batch_item_payloads(batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cache: dict[str, bool] = {}
    return [_item_payload(item, image_probe_cache=cache) for item in batch]


def _build_gemini_contents(
    payloads: list[dict[str, Any]],
    prompt: str,
) -> list[types.Content]:
    """JSON에 포함된 이미지 URL만 멀티모달로 첨부(없는 이미지는 이미 제외됨)."""
    parts: list[types.Part] = [types.Part.from_text(text=prompt)]
    attached = 0
    for meta in payloads:
        q_url = meta.get("question_image_url")
        if isinstance(q_url, str) and q_url:
            parts.append(types.Part.from_uri(file_uri=q_url, mime_type="image/png"))
            attached += 1
        for ch in meta.get("choices", []):
            if not isinstance(ch, dict):
                continue
            c_url = ch.get("image_url")
            if isinstance(c_url, str) and c_url:
                parts.append(types.Part.from_uri(file_uri=c_url, mime_type="image/png"))
                attached += 1
    if attached:
        print(f"  - Gemini 첨부 이미지 {attached}장")
    return [types.Content(role="user", parts=parts)]


def _build_prompt(payloads: list[dict[str, Any]]) -> str:
    max_choices = max((p.get("choice_count") or 5) for p in payload)
    notes_example = ", ".join(f'"{i}번: ..."' for i in range(1, max_choices + 1))
    return (
        "아래는 공인중개사 1차 기출문제(JSON)입니다. 시험 대비용 해설을 작성해줘.\n"
        "question_image_url·choices[].image_url은 보충 이미지가 실제로 있을 때만 포함된다. "
        "필드가 없으면 해당 문항·보기에는 이미지가 없는 것이므로 무시할 것.\n"
        "이미지 필드가 있는 문항은 첨부 이미지와 함께 해설에 반영할 것.\n"
        "반드시 한국어로 답변하고 JSON 형식만 반환해.\n\n"
        "여러 문제를 한 번에 보낼 수 있으므로, 반드시 id를 키로 하는 객체 형태로 반환해.\n\n"
        "중요: JSON 문법을 엄격히 지켜.\n"
        "- 코드블록(```) 금지\n"
        "- JSON 앞뒤 설명문/주석 금지\n"
        "- 배열/객체 마지막 요소 뒤 후행 콤마 금지\n\n"
        "작성 규칙:\n"
        "1) correctExplanation:\n"
        "- 정답 보기가 왜 맞는지(또는 '틀린 것' 문항이면 왜 그 보기만 틀린지) 개념으로 설명\n"
        "- 반드시 근거가 되는 법령·원리·용어를 짚을 것\n"
        "- 2~3문장, 단정형 문장 사용\n\n"
        "2) wrongAnswerNotes:\n"
        f"- 보기는 보통 5개(choice_count 참고). 각 보기마다 한 문장, 총 {max_choices}개 항목\n"
        "- 형식: '1번: ...', '2번: ...' (번호는 보기 no와 일치)\n"
        "- 맞는 이유 또는 틀린 이유를 개념 기준으로 (단순 반복 금지)\n\n"
        "3) examTip:\n"
        "- 문제 키워드·과목(subject)만 보고 정답을 좁히는 한 줄 요령\n"
        "- 암기용 문장 형태로 작성\n\n"
        "{\n"
        '  "joonggaego1_20050522_1": {\n'
        '    "correctExplanation": "...",\n'
        f'    "wrongAnswerNotes": [{notes_example}],\n'
        '    "examTip": "..."\n'
        "  }\n"
        "}\n\n"
        "문제 메타(JSON 배열):\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _build_cache(client: genai.Client) -> str:
    """시스템 지시/출력 규칙을 캐싱해 요청 비용을 절감한다."""
    cache_seed_text = (
        SYSTEM_INSTRUCTION
        + "\n출력은 반드시 JSON으로만 반환.\n"
        + "correctExplanation/wrongAnswerNotes/examTip 3개 키를 유지.\n"
        + "wrongAnswerNotes는 1번~5번 보기 각각 한 문장. 오답만이 아니라 정답 보기도 포함.\n"
        + "id 키는 입력 JSON의 id 문자열과 정확히 일치해야 함.\n"
        + "question_image_url·choices[].image_url은 이미지가 있을 때만 주어진다."
    )
    estimated_tokens = max(1, len(cache_seed_text) // 4)
    if estimated_tokens < CACHE_MIN_TOKEN_COUNT:
        raise ValueError(
            f"cache_seed_too_small: estimated={estimated_tokens}, "
            f"required>={CACHE_MIN_TOKEN_COUNT}"
        )

    cache = client.caches.create(
        model=MODEL_NAME,
        config=types.CreateCachedContentConfig(
            display_name="joonggaego_exam_ai_explanation_cache",
            system_instruction=SYSTEM_INSTRUCTION,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=cache_seed_text)],
                )
            ],
            ttl="3600s",
        ),
    )
    return cache.name


def _parse_response_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    try:
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise RuntimeError("응답 JSON 최상위는 객체(dict)여야 합니다.")
        return parsed
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        try:
            parsed, end_idx = decoder.raw_decode(cleaned)
            if not isinstance(parsed, dict):
                raise RuntimeError("응답 JSON 최상위는 객체(dict)여야 합니다.")
            remainder = cleaned[end_idx:].strip()
            if remainder:
                print(
                    "  - 경고: 응답에 JSON 외 잔여 데이터가 있어 첫 JSON 객체만 사용합니다. "
                    f"잔여 길이={len(remainder)}"
                )
            return parsed
        except json.JSONDecodeError:
            sanitized = re.sub(r",\s*([}\]])", r"\1", cleaned)
            if sanitized != cleaned:
                print("  - 경고: JSON 후행 콤마를 자동 보정해 재시도합니다.")
                parsed = json.loads(sanitized)
                if not isinstance(parsed, dict):
                    raise RuntimeError("응답 JSON 최상위는 객체(dict)여야 합니다.")
                return parsed
            raise


def _dump_parse_debug_log(
    *,
    target_path: Path,
    batch_index: int,
    total_batches: int,
    batch_ids: list[str],
    response_text: str,
    error: Exception,
) -> Path:
    DEBUG_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    safe_name = target_path.stem.replace(" ", "_")
    debug_path = DEBUG_LOG_DIR / f"{safe_name}_b{batch_index:03d}_{ts}.log"

    first_open = response_text.find("{")
    last_close = response_text.rfind("}")
    preview_head = response_text[:1000]
    preview_tail = response_text[-1000:] if len(response_text) > 1000 else response_text

    lines = [
        "=== JSON Parse Error Debug Log ===",
        f"file={target_path}",
        f"batch={batch_index}/{total_batches}",
        f"ids={batch_ids[0]}..{batch_ids[-1]}",
        f"error_type={type(error).__name__}",
        f"error={error}",
        f"response_len={len(response_text)}",
        f"first_open_brace_index={first_open}",
        f"last_close_brace_index={last_close}",
        "",
        "=== RESPONSE HEAD (first 1000 chars) ===",
        preview_head,
        "",
        "=== RESPONSE TAIL (last 1000 chars) ===",
        preview_tail,
        "",
        "=== FULL RESPONSE ===",
        response_text,
        "",
    ]
    debug_path.write_text("\n".join(lines), encoding="utf-8")
    return debug_path


def _resolve_input_path(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p.resolve()


def _target_paths(input_path: Path) -> list[Path]:
    if input_path.is_dir():
        return sorted(
            p
            for p in input_path.glob("*.json")
            if p.is_file() and p.name != SESSION_MANIFEST_NAME
        )
    return [input_path]


def needs_ai_explanation(item: dict[str, Any]) -> bool:
    """aiExplanation이 없거나 비어 있거나 필수 필드가 불완전하면 True."""
    ae = item.get("aiExplanation")
    if ae is None:
        return True
    if not isinstance(ae, dict):
        return True
    ce = ae.get("correctExplanation")
    if not isinstance(ce, str) or not ce.strip():
        return True
    tip = ae.get("examTip")
    if not isinstance(tip, str) or not tip.strip():
        return True
    notes = ae.get("wrongAnswerNotes")
    if not isinstance(notes, list) or len(notes) == 0:
        return True
    if not all(isinstance(x, str) and x.strip() for x in notes):
        return True
    choices = item.get("choices", [])
    if isinstance(choices, list) and len(choices) > 0 and len(notes) < len(choices):
        return True
    return False


def _chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def generate_ai_explanations(
    input_path: Path,
    batch_size: int,
    skip_existing: bool,
    missing_only: bool,
    fail_fast: bool,
) -> None:
    client, client_mode = _build_genai_client()
    print(
        "[설정] "
        f"model={MODEL_NAME}, batch_size={batch_size}, "
        f"skip_existing={skip_existing}, missing_only={missing_only}, "
        f"fail_fast={fail_fast}, stuck_timeout={STUCK_TIMEOUT_SECONDS}s, "
        f"max_retries={MAX_RETRIES}, client={client_mode}"
    )
    cache_name: str | None = None
    try:
        cache_name = _build_cache(client)
        print(f"컨텍스트 캐시 사용: {cache_name}")
    except Exception as e:
        print(f"캐시 미사용(일반 호출로 진행): {e}")

    target_paths = _target_paths(input_path)
    if not target_paths:
        raise FileNotFoundError(f"처리할 JSON 파일이 없습니다: {input_path}")

    total_files = len(target_paths)
    total_processed = 0
    total_failed_batches = 0
    for file_index, target_path in enumerate(target_paths, start=1):
        file_start = time.perf_counter()
        data = json.loads(target_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"입력 JSON은 문제 객체 배열이어야 합니다: {target_path}")

        print(f"\n[{file_index}/{len(target_paths)}] 파일 처리: {target_path}")
        source_items = data
        if missing_only:
            source_items = [item for item in data if needs_ai_explanation(item)]
            skipped_count = len(data) - len(source_items)
            if skipped_count:
                print(f"  - 이미 완전한 aiExplanation 스킵: {skipped_count}개")
        elif skip_existing:
            source_items = [item for item in data if "aiExplanation" not in item]
            skipped_count = len(data) - len(source_items)
            if skipped_count:
                print(f"  - 기존 aiExplanation 스킵: {skipped_count}개")

        if not source_items:
            print("  - 처리할 신규 문항이 없어 파일 저장을 건너뜁니다.")
            continue

        batches = _chunked(source_items, batch_size)
        processed = 0
        failed_batches: list[str] = []
        for batch_index, batch in enumerate(batches, start=1):
            batch_ids = [str(item.get("id")) for item in batch]
            print(
                f"  - 배치 시작 [{batch_index}/{len(batches)}] "
                f"size={len(batch)} ids={batch_ids[0]}..{batch_ids[-1]}"
            )
            payloads = _batch_item_payloads(batch)
            prompt = _build_prompt(payloads)
            gemini_contents = _build_gemini_contents(payloads, prompt)
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            )
            if cache_name:
                config.cached_content = cache_name

            batch_start = time.perf_counter()
            try:
                resp = _generate_with_timeout_and_retry(
                    client,
                    contents=gemini_contents,
                    config=config,
                    batch_label=(
                        f"{target_path.name} [{batch_index}/{len(batches)}] "
                        f"ids={batch_ids[0]}..{batch_ids[-1]}"
                    ),
                )
            except StuckTimeoutError:
                raise
            except Exception as e:
                print(f"배치 실패: {e}")
                msg = (
                    f"배치 실패 [{batch_index}/{len(batches)}] "
                    f"ids={batch_ids}, batch_size={len(batch)}, "
                    f"error_type={type(e).__name__}: {e}"
                )
                if fail_fast:
                    raise RuntimeError(msg) from e
                failed_batches.append(msg)
                total_failed_batches += 1
                print(f"  - {msg}")
                continue
            response_text = _response_text(resp)
            if not response_text:
                raise RuntimeError(f"{target_path} 배치 응답이 비어 있습니다.")

            try:
                explanation = _parse_response_json(response_text)
            except json.JSONDecodeError as e:
                debug_path = _dump_parse_debug_log(
                    target_path=target_path,
                    batch_index=batch_index,
                    total_batches=len(batches),
                    batch_ids=batch_ids,
                    response_text=response_text,
                    error=e,
                )
                print(
                    f"배치 JSON 파싱 실패 [{batch_index}/{len(batches)}] "
                    f"ids={batch_ids[0]}..{batch_ids[-1]}"
                )
                print(f"  - 디버그 로그 저장: {debug_path}")
                print(f"  - 응답 길이: {len(response_text)}자")
                raise
            if not isinstance(explanation, dict):
                raise RuntimeError("배치 응답 형식이 올바르지 않습니다(dict 필요).")

            for item in batch:
                item_id = str(item.get("id"))
                if item_id not in explanation:
                    raise RuntimeError(f"배치 응답에 id 누락: {item_id}")
                item["aiExplanation"] = explanation[item_id]
                processed += 1
                total_processed += 1

            target_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            print(
                f"  - 배치 [{batch_index}/{len(batches)}] 완료 "
                f"(누적 {processed}/{len(source_items)}, "
                f"소요 {time.perf_counter() - batch_start:.1f}s)"
            )
        print(f"파일 반영 완료: {target_path}")
        if failed_batches:
            print(f"  - 실패 배치 {len(failed_batches)}건")
            for failed in failed_batches:
                print(f"    * {failed}")
        print(
            f"[{file_index}/{total_files}] 파일 완료: {target_path} "
            f"(소요 {time.perf_counter() - file_start:.1f}s)"
        )

    print(
        f"\n전체 완료: 파일 {total_files}개, 처리 문항 {total_processed}개, "
        f"실패 배치 {total_failed_batches}건"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="joonggaego assets/jsons 기출 JSON에 Gemini 해설(aiExplanation) 추가"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_JSON_DIR.relative_to(REPO_ROOT)),
        help="JSON 파일 또는 폴더(기본 assets/jsons, exam-sessions.json 제외)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="한 번의 API 호출에 포함할 문제 수 (기본 1, 권장 3~5)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="이미 aiExplanation 키가 있는 문항은 건너뜁니다.",
    )
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="aiExplanation이 없거나 불완전한 문항만 처리합니다.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="배치 실패 시 즉시 중단합니다(기본은 실패 배치 건너뛰고 계속).",
    )
    args = parser.parse_args()
    if args.batch_size < 1:
        raise ValueError("--batch-size는 1 이상이어야 합니다.")
    if args.missing_only and args.skip_existing:
        raise ValueError("--missing-only 와 --skip-existing 는 함께 쓸 수 없습니다.")

    input_path = _resolve_input_path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"경로가 없습니다: {input_path}")

    restart_count = 0
    while True:
        try:
            generate_ai_explanations(
                input_path,
                batch_size=args.batch_size,
                skip_existing=args.skip_existing,
                missing_only=args.missing_only,
                fail_fast=args.fail_fast,
            )
            break
        except StuckTimeoutError as e:
            if not AUTO_RESTART_ON_STUCK:
                raise
            restart_count += 1
            print(f"\n[자동 재시작] 스턱 감지: {e}")
            if restart_count > MAX_AUTO_RESTARTS:
                raise RuntimeError(
                    f"스턱으로 인한 자동 재시작 한도({MAX_AUTO_RESTARTS}회)를 초과했습니다."
                ) from e
            print(
                f"[자동 재시작] {restart_count}/{MAX_AUTO_RESTARTS}회, "
                f"{RESTART_DELAY_SECONDS}s 후 재시도"
            )
            time.sleep(RESTART_DELAY_SECONDS)


if __name__ == "__main__":
    main()
