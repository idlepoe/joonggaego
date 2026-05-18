"""Gemini로 기출 JSON의 question_text·choices[].text 띄어쓰기만 교정.

`generate_ai_explanations.py`의 클라이언트·재시도·JSON 파싱·배치 저장 흐름을 따른다.
이미지·aiExplanation 등 다른 필드는 변경하지 않는다.

배치 크기 권장:
  - 기본 5문항/호출 (~문항당 지문+보기 5줄, 회차 80문항 기준 약 16회 호출)
  - 띄어쓰기만 다루므로 해설 생성(기본 1~3)보다 크게 잡을 수 있으나,
    id 누락·JSON 깨짐을 줄이려면 5~8을 권장 (10 이상은 비권장)

사용 예:
  python scripts/fix_spacing_with_ai.py --input assets/jsons/2005-05-22.json
  python scripts/fix_spacing_with_ai.py --input assets/jsons/2005-05-22.json --dry-run
  python scripts/fix_spacing_with_ai.py --input assets/jsons --batch-size 5
  python scripts/fix_spacing_with_ai.py --input assets/jsons --from-file 2013-10-27.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TextIO

from google.genai import types

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from generate_ai_explanations import (  # noqa: E402
    AUTO_RESTART_ON_STUCK,
    MAX_AUTO_RESTARTS,
    MAX_RETRIES,
    MODEL_NAME,
    REPO_ROOT,
    RESTART_DELAY_SECONDS,
    STUCK_TIMEOUT_SECONDS,
    StuckTimeoutError,
    _build_genai_client,
    _chunked,
    _dump_parse_debug_log,
    _generate_with_timeout_and_retry,
    _parse_response_json,
    _resolve_input_path,
    _response_text,
    _target_paths,
)

DEFAULT_BATCH_SIZE = 5
DEFAULT_TIMEOUT_SECONDS = STUCK_TIMEOUT_SECONDS
DEFAULT_BATCH_RETRIES = 3
DEFAULT_BATCH_RETRY_DELAY = 5.0
LOG_DIR = REPO_ROOT / "logs" / "fix_spacing"


class RunLogger:
    """콘솔(stdout)과 로그 파일에 동일한 내용을 기록한다."""

    def __init__(self, log_path: Path | None) -> None:
        self._log_path = log_path
        self._file: TextIO | None = None
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(line_buffering=True)
            except Exception:
                pass
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._file = log_path.open("a", encoding="utf-8", buffering=1)
            self._emit(
                f"=== fix_spacing_with_ai 시작 {datetime.now().isoformat(timespec='seconds')} ==="
            )

    def close(self) -> None:
        if self._file is not None:
            self._emit(f"=== 종료 {datetime.now().isoformat(timespec='seconds')} ===")
            self._file.close()
            self._file = None

    @property
    def path(self) -> Path | None:
        return self._log_path

    def emit(self, message: str) -> None:
        """콘솔·파일 동시 출력 (외부 모듈 콜백용)."""
        self._emit(message)

    def _emit(self, message: str) -> None:
        print(message, flush=True)
        if self._file is not None:
            self._file.write(message + "\n")
            self._file.flush()

    def log(self, message: str = "") -> None:
        self._emit(message)

    def warn(self, message: str) -> None:
        self._emit(f"[경고] {message}")

    def error(self, message: str) -> None:
        self._emit(f"[오류] {message}")


def _default_log_path() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOG_DIR / f"fix_spacing_{ts}.log"


def _normalize_json_filename(name: str) -> str:
    return name if name.endswith(".json") else f"{name}.json"


def _filter_paths_from(
    paths: list[Path], from_file: str | None, logger: RunLogger
) -> list[Path]:
    if not from_file:
        return paths
    start_name = _normalize_json_filename(from_file.strip())
    names = [p.name for p in paths]
    if start_name not in names:
        raise FileNotFoundError(
            f"--from-file={from_file!r} 에 해당하는 파일이 없습니다. "
            f"후보: {', '.join(names)}"
        )
    idx = names.index(start_name)
    if idx > 0:
        skipped = [p.name for p in paths[:idx]]
        logger.log(f"[from-file] 건너뜀 {len(skipped)}개: {', '.join(skipped)}")
    return paths[idx:]


def _call_api_with_batch_retries(
    call: Callable[[], Any],
    *,
    batch_label: str,
    batch_retries: int,
    batch_retry_delay: float,
    fail_fast: bool,
    logger: RunLogger,
) -> Any:
    """배치 단위로 API 호출을 재시도한다(타임아웃·일시 오류 포함)."""
    last_error: Exception | None = None
    for attempt in range(1, batch_retries + 1):
        try:
            if attempt > 1:
                logger.log(f"  - API 호출 시도 {attempt}/{batch_retries} ({batch_label})")
            return call()
        except StuckTimeoutError as e:
            last_error = e
            if attempt >= batch_retries:
                break
            wait = batch_retry_delay * attempt
            logger.warn(
                f"배치 스턱 재시도 {attempt}/{batch_retries} ({batch_label}) | {wait:.1f}s 후"
            )
            time.sleep(wait)
        except Exception as e:
            last_error = e
            if attempt >= batch_retries:
                break
            wait = batch_retry_delay * attempt
            logger.warn(
                f"배치 실패 재시도 {attempt}/{batch_retries} ({batch_label}) "
                f"{type(e).__name__}: {e} | {wait:.1f}s 후"
            )
            time.sleep(wait)
    if last_error is None:
        raise RuntimeError(f"{batch_label} 배치 재시도 루프가 비정상 종료되었습니다.")
    if fail_fast:
        raise RuntimeError(f"{batch_label} 배치 최종 실패") from last_error
    raise last_error

SYSTEM_INSTRUCTION = (
    "당신은 띄어쓰기(공백)만 수정하는 교정기입니다. "
    "공인중개사 1차 기출의 question_text와 choices[].text에 적용합니다.\n"
    "절대 규칙:\n"
    "1) 공백(스페이스·탭·줄바꿈)만 추가하거나 제거할 수 있습니다.\n"
    "2) 공백을 제외한 모든 글자(한글·영문·숫자·구두점·괄호·기호)는 "
    "입력과 완전히 같은 순서·같은 개수로 유지해야 합니다.\n"
    "3) 맞춤법·어미·조사·단어 치환·띄어읽기로 인한 글자 변경은 금지합니다.\n"
    "4) 오탈자 수정, 동의어 교체, 문장 다듬기, 보기 순서·개수 변경 금지.\n"
    "5) PDF 줄바꿈으로 생긴 잘못된 공백은 제거하고, 붙어 쓴 부분에만 공백을 넣으세요."
)


def _spacing_payload(item: dict[str, Any]) -> dict[str, Any]:
    choices_out: list[dict[str, Any]] = []
    for ch in item.get("choices") or []:
        if not isinstance(ch, dict):
            continue
        choices_out.append({"no": ch.get("no"), "text": ch.get("text", "")})
    return {
        "id": item.get("id"),
        "question_number": item.get("question_number"),
        "question_text": item.get("question_text", ""),
        "choices": choices_out,
    }


def _build_prompt(payloads: list[dict[str, Any]]) -> str:
    return (
        "아래 JSON 배열의 각 문항에 대해 question_text와 choices[].text의 "
        "띄어쓰기(공백)만 교정하세요. "
        "한글·영문·숫자·구두점·괄호 등 글자는 바꾸지 마세요.\n"
        "다른 필드는 출력에 포함하지 마세요.\n"
        "반드시 한국어 JSON 객체만 반환하고, 최상위 키는 각 문항 id 문자열과 동일해야 합니다.\n"
        "코드블록(```)과 설명문은 금지합니다.\n\n"
        "출력 형식 예:\n"
        "{\n"
        '  "joonggaego1_20050522_1": {\n'
        '    "question_text": "교정된 지문",\n'
        '    "choices": [\n'
        '      {"no": 1, "text": "교정된 보기1"},\n'
        '      {"no": 2, "text": "교정된 보기2"}\n'
        "    ]\n"
        "  }\n"
        "}\n\n"
        "입력:\n"
        f"{json.dumps(payloads, ensure_ascii=False, indent=2)}"
    )


def _apply_spacing_patch(
    item: dict[str, Any],
    patch: dict[str, Any],
    *,
    logger: RunLogger,
) -> tuple[int, int]:
    """(지문 변경 수, 보기 변경 수)"""
    stem_changes = 0
    choice_changes = 0
    item_id = item.get("id")

    old_stem = item.get("question_text", "")
    if not isinstance(old_stem, str):
        old_stem = ""
    new_stem = patch.get("question_text")
    if isinstance(new_stem, str) and new_stem != old_stem:
        item["question_text"] = new_stem
        stem_changes = 1

    patch_choices = patch.get("choices")
    if not isinstance(patch_choices, list):
        raise RuntimeError(f"choices 배열 누락: {item_id}")

    by_no: dict[int, dict[str, Any]] = {}
    for ch in item.get("choices") or []:
        if isinstance(ch, dict) and ch.get("no") is not None:
            by_no[int(ch["no"])] = ch

    for pch in patch_choices:
        if not isinstance(pch, dict):
            continue
        no = pch.get("no")
        new_text = pch.get("text")
        if no is None or not isinstance(new_text, str):
            continue
        key = int(no)
        if key not in by_no:
            logger.warn(f"id={item_id} choice no={no}: 원문에 없는 보기 (건너뜀)")
            continue
        old_text = by_no[key].get("text", "")
        if not isinstance(old_text, str):
            old_text = ""
        if new_text != old_text:
            by_no[key]["text"] = new_text
            choice_changes += 1

    patched_nos = {
        int(pch["no"])
        for pch in patch_choices
        if isinstance(pch, dict) and pch.get("no") is not None
    }
    missing_nos = sorted(set(by_no.keys()) - patched_nos)
    if missing_nos:
        logger.warn(f"id={item_id}: 응답에 없는 보기 no={missing_nos}")
    return stem_changes, choice_changes


def fix_spacing_with_ai(
    input_path: Path,
    *,
    batch_size: int,
    dry_run: bool,
    fail_fast: bool,
    from_file: str | None,
    timeout_seconds: float,
    batch_retries: int,
    batch_retry_delay: float,
    logger: RunLogger,
) -> None:
    target_paths = _filter_paths_from(_target_paths(input_path), from_file, logger)
    if not target_paths:
        raise FileNotFoundError(f"처리할 JSON이 없습니다: {input_path}")

    total_batches_planned = 0
    for target_path in target_paths:
        data = json.loads(target_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            total_batches_planned += len(_chunked(data, batch_size))

    logger.log(
        "[설정] "
        f"model={MODEL_NAME}, batch_size={batch_size}, dry_run={dry_run}, "
        f"fail_fast={fail_fast}, timeout={timeout_seconds}s, "
        f"api_retries={MAX_RETRIES}, batch_retries={batch_retries}, "
        f"batch_retry_delay={batch_retry_delay}s, "
        f"files={len(target_paths)}, planned_batches={total_batches_planned}"
    )
    if logger.path:
        logger.log(f"[로그 파일] {logger.path}")

    if dry_run:
        for target_path in target_paths:
            data = json.loads(target_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                logger.log(f"  [건너뜀] 배열 아님: {target_path}")
                continue
            batches = _chunked(data, batch_size)
            logger.log(
                f"{target_path.name}: 문항 {len(data)}개, "
                f"예상 API 호출 {len(batches)}회 (배치당 최대 {batch_size}문항)"
            )
        return

    client, client_mode = _build_genai_client()
    logger.log(f"클라이언트: {client_mode}")

    total_stems = 0
    total_choices = 0
    total_failed = 0
    global_batch_done = 0
    run_start = time.perf_counter()

    for file_index, target_path in enumerate(target_paths, start=1):
        file_start = time.perf_counter()
        data = json.loads(target_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"배열 JSON이어야 합니다: {target_path}")

        batches = _chunked(data, batch_size)
        logger.log("")
        logger.log(
            f"[파일 시작 {file_index}/{len(target_paths)}] {target_path.name} "
            f"— 문항 {len(data)}개, 배치 {len(batches)}개"
        )

        file_stems = 0
        file_choices = 0
        for batch_index, batch in enumerate(batches, start=1):
            batch_ids = [str(item.get("id")) for item in batch]
            global_batch_done += 1
            pct = (
                100.0 * global_batch_done / total_batches_planned
                if total_batches_planned
                else 0.0
            )
            logger.log(
                f"  [배치 시작 {batch_index}/{len(batches)} | "
                f"전체 {global_batch_done}/{total_batches_planned} ({pct:.1f}%)] "
                f"size={len(batch)} ids={batch_ids[0]}..{batch_ids[-1]}"
            )
            payloads = [_spacing_payload(item) for item in batch]
            prompt = _build_prompt(payloads)
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0,
                system_instruction=SYSTEM_INSTRUCTION,
            )

            batch_label = (
                f"{target_path.name} [{batch_index}/{len(batches)}] "
                f"ids={batch_ids[0]}..{batch_ids[-1]}"
            )
            batch_start = time.perf_counter()
            logger.log(f"  - API 요청 중… ({batch_label})")
            try:
                resp = _call_api_with_batch_retries(
                    lambda: _generate_with_timeout_and_retry(
                        client,
                        contents=prompt,
                        config=config,
                        batch_label=batch_label,
                        timeout_seconds=timeout_seconds,
                        log_fn=logger.emit,
                    ),
                    batch_label=batch_label,
                    batch_retries=batch_retries,
                    batch_retry_delay=batch_retry_delay,
                    fail_fast=fail_fast,
                    logger=logger,
                )
            except Exception as e:
                msg = (
                    f"배치 최종 실패 [{batch_index}/{len(batches)}] "
                    f"ids={batch_ids}: {type(e).__name__}: {e}"
                )
                if fail_fast:
                    raise RuntimeError(msg) from e
                logger.error(msg)
                total_failed += 1
                continue

            response_text = _response_text(resp)
            logger.log(f"  - API 응답 수신 ({len(response_text)}자)")
            if not response_text:
                raise RuntimeError(f"빈 응답: {target_path} 배치 {batch_index}")

            parsed: dict[str, Any] | None = None
            parse_error: json.JSONDecodeError | None = None
            for parse_attempt in range(1, batch_retries + 1):
                try:
                    parsed = _parse_response_json(response_text)
                    parse_error = None
                    break
                except json.JSONDecodeError as e:
                    parse_error = e
                    if parse_attempt >= batch_retries:
                        break
                    wait = batch_retry_delay * parse_attempt
                    logger.warn(
                        f"JSON 파싱 재시도 {parse_attempt}/{batch_retries} "
                        f"({batch_label}) | {wait:.1f}s 후 API 재호출"
                    )
                    time.sleep(wait)
                    try:
                        resp = _call_api_with_batch_retries(
                            lambda: _generate_with_timeout_and_retry(
                                client,
                                contents=prompt,
                                config=config,
                                batch_label=batch_label,
                                timeout_seconds=timeout_seconds,
                                log_fn=logger.emit,
                            ),
                            batch_label=batch_label,
                            batch_retries=batch_retries,
                            batch_retry_delay=batch_retry_delay,
                            fail_fast=fail_fast,
                            logger=logger,
                        )
                        response_text = _response_text(resp)
                        if not response_text:
                            raise RuntimeError(f"빈 응답: {target_path} 배치 {batch_index}")
                    except Exception as api_e:
                        if fail_fast:
                            raise RuntimeError(
                                f"JSON 파싱 재호출 실패 ({batch_label})"
                            ) from api_e
                        logger.error(f"JSON 파싱 재호출 실패: {api_e}")
                        break
            if parsed is None:
                debug_path = _dump_parse_debug_log(
                    target_path=target_path,
                    batch_index=batch_index,
                    total_batches=len(batches),
                    batch_ids=batch_ids,
                    response_text=response_text,
                    error=parse_error or json.JSONDecodeError("unknown", "", 0),
                )
                logger.error(f"JSON 파싱 최종 실패, 디버그: {debug_path}")
                if fail_fast:
                    raise RuntimeError(f"JSON 파싱 실패 ({batch_label})") from parse_error
                total_failed += 1
                continue

            batch_stems = 0
            batch_choices = 0
            for item in batch:
                item_id = str(item.get("id"))
                if item_id not in parsed:
                    raise RuntimeError(f"응답에 id 누락: {item_id}")
                patch = parsed[item_id]
                if not isinstance(patch, dict):
                    raise RuntimeError(f"id={item_id} 값이 객체가 아닙니다.")
                s, c = _apply_spacing_patch(item, patch, logger=logger)
                batch_stems += s
                batch_choices += c

            target_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            file_stems += batch_stems
            file_choices += batch_choices
            logger.log(
                f"  [배치 완료] {time.perf_counter() - batch_start:.1f}s "
                f"— 지문 {batch_stems}, 보기 {batch_choices} 수정 | "
                f"파일 누적 지문 {file_stems}, 보기 {file_choices}"
            )

        total_stems += file_stems
        total_choices += file_choices
        logger.log(
            f"[파일 완료 {file_index}/{len(target_paths)}] {target_path.name} "
            f"{time.perf_counter() - file_start:.1f}s — "
            f"지문 {file_stems}, 보기 {file_choices} | 저장됨"
        )

    elapsed = time.perf_counter() - run_start
    logger.log(
        f"\n[전체 완료] {elapsed:.1f}s — "
        f"지문 {total_stems}건, 보기 {total_choices}건 수정, 실패 배치 {total_failed}건"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str((REPO_ROOT / "assets" / "jsons").relative_to(REPO_ROOT)),
        help="JSON 파일 또는 폴더",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"한 번의 API 호출당 문항 수 (기본 {DEFAULT_BATCH_SIZE}, 권장 5~8)",
    )
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 호출 횟수만 집계")
    parser.add_argument("--fail-fast", action="store_true", help="배치 실패 시 즉시 중단")
    parser.add_argument(
        "--from-file",
        metavar="NAME",
        help="폴더 입력 시 이 파일명부터 처리 (예: 2013-10-27.json)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"API 응답 대기 초 (기본 {DEFAULT_TIMEOUT_SECONDS}, 호출당 최대 {MAX_RETRIES}회 재시도)",
    )
    parser.add_argument(
        "--batch-retries",
        type=int,
        default=DEFAULT_BATCH_RETRIES,
        help=f"배치 단위 추가 재시도 횟수 (기본 {DEFAULT_BATCH_RETRIES})",
    )
    parser.add_argument(
        "--batch-retry-delay",
        type=float,
        default=DEFAULT_BATCH_RETRY_DELAY,
        help=f"배치 재시도 간 대기 초 (기본 {DEFAULT_BATCH_RETRY_DELAY})",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="처리 로그 파일 경로 (기본 logs/fix_spacing/fix_spacing_YYYYMMDD_HHMMSS.log)",
    )
    parser.add_argument(
        "--no-log-file",
        action="store_true",
        help="로그 파일 없이 콘솔에만 출력",
    )
    args = parser.parse_args()

    if args.batch_size < 1:
        raise ValueError("--batch-size는 1 이상이어야 합니다.")
    if args.batch_size > 10:
        print("경고: batch-size가 10을 넘으면 JSON 누락·오류 가능성이 커집니다.", file=sys.stderr)
    if args.timeout <= 0:
        raise ValueError("--timeout은 0보다 커야 합니다.")
    if args.batch_retries < 1:
        raise ValueError("--batch-retries는 1 이상이어야 합니다.")

    root = _resolve_input_path(args.input)
    if not root.exists():
        raise FileNotFoundError(f"경로 없음: {root}")

    log_path: Path | None = None
    if not args.no_log_file:
        log_path = args.log_file if args.log_file is not None else _default_log_path()
        if not log_path.is_absolute():
            log_path = REPO_ROOT / log_path

    logger = RunLogger(log_path)
    exit_code = 1
    try:
        restart_count = 0
        while True:
            try:
                fix_spacing_with_ai(
                    root,
                    batch_size=args.batch_size,
                    dry_run=args.dry_run,
                    fail_fast=args.fail_fast,
                    from_file=args.from_file,
                    timeout_seconds=args.timeout,
                    batch_retries=args.batch_retries,
                    batch_retry_delay=args.batch_retry_delay,
                    logger=logger,
                )
                exit_code = 0
                break
            except StuckTimeoutError as e:
                if not AUTO_RESTART_ON_STUCK or args.dry_run:
                    raise
                restart_count += 1
                if restart_count > MAX_AUTO_RESTARTS:
                    raise RuntimeError(
                        f"자동 재시작 한도({MAX_AUTO_RESTARTS}회) 초과"
                    ) from e
                logger.warn(
                    f"자동 재시작 {restart_count}/{MAX_AUTO_RESTARTS}, "
                    f"{RESTART_DELAY_SECONDS}s 대기: {e}"
                )
                time.sleep(RESTART_DELAY_SECONDS)
    finally:
        logger.close()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
