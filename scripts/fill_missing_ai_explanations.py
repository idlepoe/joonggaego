"""aiExplanation이 누락되었거나 불완전한 문항만 골라 해설을 생성한다.

`generate_ai_explanations.py`의 API/배치/재시도 로직을 그대로 쓰고,
필터만 `needs_ai_explanation` 기준으로 제한한다.

사용 예시:
  python scripts/fill_missing_ai_explanations.py --input assets/jsons
  python scripts/fill_missing_ai_explanations.py --input assets/jsons --dry-run
  python scripts/fill_missing_ai_explanations.py --input assets/jsons/2005-05-22.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import TextIO

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from generate_ai_explanations import (  # noqa: E402
    AUTO_RESTART_ON_STUCK,
    DEFAULT_JSON_DIR,
    MAX_AUTO_RESTARTS,
    REPO_ROOT,
    RESTART_DELAY_SECONDS,
    StuckTimeoutError,
    _resolve_input_path,
    _target_paths,
    generate_ai_explanations,
    needs_ai_explanation,
)

LOG_DIR = REPO_ROOT / "logs" / "fill_missing_ai_explanations"


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
                f"=== fill_missing_ai_explanations 시작 "
                f"{datetime.now().isoformat(timespec='seconds')} ==="
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
    return LOG_DIR / f"fill_missing_ai_explanations_{ts}.log"


def _summarize_work(
    paths: list[Path], batch_size: int
) -> tuple[int, int, int, list[tuple[str, int, int]]]:
    """(전체 문항, 누락 문항, 예상 배치 수, 파일별 (전체, 누락)) 반환."""
    total_items = 0
    total_missing = 0
    total_batches = 0
    per_file: list[tuple[str, int, int]] = []
    for p in paths:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        missing = [item for item in data if needs_ai_explanation(item)]
        n_missing = len(missing)
        n_all = len(data)
        total_items += n_all
        total_missing += n_missing
        if n_missing:
            batches = (n_missing + batch_size - 1) // batch_size
            total_batches += batches
            per_file.append((p.name, n_all, n_missing))
    return total_items, total_missing, total_batches, per_file


def _dry_run(input_path: Path, batch_size: int, logger: RunLogger) -> None:
    paths = _target_paths(input_path)
    if not paths:
        logger.log(f"JSON 파일이 없습니다: {input_path}")
        return

    total_items, total_missing, total_batches, per_file = _summarize_work(
        paths, batch_size
    )
    logger.log(
        f"[dry-run] 파일 {len(paths)}개, 전체 문항 {total_items}개, "
        f"보강 필요 {total_missing}개, 예상 API 호출 {total_batches}회 "
        f"(batch_size={batch_size})"
    )
    for name, n_all, n_missing in per_file:
        batches = (n_missing + batch_size - 1) // batch_size
        logger.log(
            f"  {name}: 누락/불완전 {n_missing}개 / 전체 {n_all}개 "
            f"→ API {batches}회"
        )
    files_with_gaps = len(per_file)
    logger.log(
        f"\n요약: 파일 {len(paths)}개 중 보강 필요 {files_with_gaps}개, "
        f"문항 {total_missing}개"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="aiExplanation 누락·불완전 문항만 채움 (assets/jsons 스캔)"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_JSON_DIR.relative_to(REPO_ROOT)),
        help="JSON 파일 또는 폴더(기본 assets/jsons)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="한 번의 API 호출에 넣을 문제 수 (기본 1)",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="배치 실패 시 즉시 중단",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="API 호출 없이 누락/불완전 문항 수만 집계",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help=(
            "처리 로그 파일 경로 "
            "(기본 logs/fill_missing_ai_explanations/"
            "fill_missing_ai_explanations_YYYYMMDD_HHMMSS.log)"
        ),
    )
    parser.add_argument(
        "--no-log-file",
        action="store_true",
        help="로그 파일 없이 콘솔에만 출력",
    )
    args = parser.parse_args()
    if args.batch_size < 1:
        raise ValueError("--batch-size는 1 이상이어야 합니다.")

    root = _resolve_input_path(args.input)
    if not root.exists():
        raise FileNotFoundError(f"경로가 없습니다: {root}")

    log_path: Path | None = None
    if not args.no_log_file:
        log_path = args.log_file if args.log_file is not None else _default_log_path()
        if not log_path.is_absolute():
            log_path = REPO_ROOT / log_path

    logger = RunLogger(log_path)
    exit_code = 1
    try:
        paths = _target_paths(root)
        if not paths:
            logger.error(f"처리할 JSON 파일이 없습니다: {root}")
            return 1

        logger.log(f"[입력] {root}")
        logger.log(f"[대상 파일] {len(paths)}개")
        if logger.path:
            logger.log(f"[로그 파일] {logger.path}")

        total_items, total_missing, total_batches, per_file = _summarize_work(
            paths, args.batch_size
        )
        for name, n_all, n_missing in per_file:
            batches = (n_missing + args.batch_size - 1) // args.batch_size
            logger.log(
                f"  - {name}: 누락/불완전 {n_missing}개 / 전체 {n_all}개 "
                f"→ 예상 API {batches}회"
            )
        logger.log(
            f"[사전 집계] 전체 문항 {total_items}개, 보강 필요 {total_missing}개, "
            f"예상 API 호출 {total_batches}회 (batch_size={args.batch_size}, "
            f"fail_fast={args.fail_fast})"
        )

        if args.dry_run:
            logger.log("")
            _dry_run(root, args.batch_size, logger)
            exit_code = 0
            return exit_code

        if total_missing == 0:
            logger.log("보강할 문항이 없어 종료합니다.")
            exit_code = 0
            return exit_code

        run_start = time.perf_counter()
        restart_count = 0
        while True:
            try:
                generate_ai_explanations(
                    root,
                    batch_size=args.batch_size,
                    skip_existing=False,
                    missing_only=True,
                    fail_fast=args.fail_fast,
                    log_fn=logger.emit,
                )
                exit_code = 0
                break
            except StuckTimeoutError as e:
                if not AUTO_RESTART_ON_STUCK:
                    raise
                restart_count += 1
                logger.warn(
                    f"자동 재시작 {restart_count}/{MAX_AUTO_RESTARTS}, "
                    f"{RESTART_DELAY_SECONDS}s 대기: {e}"
                )
                if restart_count > MAX_AUTO_RESTARTS:
                    raise RuntimeError(
                        f"스턱으로 인한 자동 재시작 한도({MAX_AUTO_RESTARTS}회)를 초과했습니다."
                    ) from e
                time.sleep(RESTART_DELAY_SECONDS)

        logger.log(
            f"\n[실행 완료] 총 소요 {time.perf_counter() - run_start:.1f}s, "
            f"자동 재시작 {restart_count}회"
        )
    finally:
        logger.close()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
