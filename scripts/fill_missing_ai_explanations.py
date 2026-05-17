"""aiExplanation이 누락되었거나 불완전한 문항만 골라 해설을 생성한다.

`generate_ai_explanations.py`의 API/배치/재시도 로직을 그대로 쓰고,
필터만 `needs_ai_explanation` 기준으로 제한한다.

사용 예시:
  # exams 폴더 전체 — 누락/불완전만 API로 채움
  python scripts/fill_missing_ai_explanations.py --input assets/json/exams

  # 먼저 전체 스캔( API 없이 누락 개수만 집계 )
  python scripts/fill_missing_ai_explanations.py --input assets/json/exams --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from generate_ai_explanations import (  # noqa: E402
    AUTO_RESTART_ON_STUCK,
    MAX_AUTO_RESTARTS,
    RESTART_DELAY_SECONDS,
    StuckTimeoutError,
    _target_paths,
    generate_ai_explanations,
    needs_ai_explanation,
)


def _dry_run(input_path: Path) -> None:
    paths = _target_paths(input_path)
    if not paths:
        print(f"JSON 파일이 없습니다: {input_path}")
        return
    total_missing = 0
    files_with_gaps = 0
    for p in paths:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            print(f"  [건너뜀] 배열이 아님: {p}")
            continue
        missing = [item for item in data if needs_ai_explanation(item)]
        n = len(missing)
        if n:
            files_with_gaps += 1
            total_missing += n
            print(f"{p.name}: 누락/불완전 {n}개 / 전체 {len(data)}개")
    print(
        f"\n요약: 파일 {len(paths)}개 중 보강 필요 {files_with_gaps}개, "
        f"문항 {total_missing}개"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="aiExplanation 누락·불완전 문항만 채움 (exams 전체 스캔용)"
    )
    parser.add_argument(
        "--input",
        default="assets/json/exams",
        help="JSON 파일 또는 폴더(폴더면 *.json 전부)",
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
    args = parser.parse_args()
    if args.batch_size < 1:
        raise ValueError("--batch-size는 1 이상이어야 합니다.")

    root = Path(args.input)
    if not root.exists():
        raise FileNotFoundError(f"경로가 없습니다: {root}")

    if args.dry_run:
        _dry_run(root)
        return

    restart_count = 0
    while True:
        try:
            generate_ai_explanations(
                root,
                batch_size=args.batch_size,
                skip_existing=False,
                missing_only=True,
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
