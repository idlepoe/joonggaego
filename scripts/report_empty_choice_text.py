"""choices[].text가 비어 있는 문항을 assets/jsons에서 찾아 목록으로 출력."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JSON_DIR = REPO_ROOT / "assets" / "jsons"


def find_empty_choice_text(json_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(json_dir.glob("*.json")):
        if path.name == "exam-sessions.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        for q in data:
            empty_nos: list[int | None] = []
            for c in q.get("choices") or []:
                if not isinstance(c, dict):
                    continue
                text = c.get("text")
                if text is None or (isinstance(text, str) and not text.strip()):
                    no = c.get("no")
                    empty_nos.append(int(no) if no is not None else None)
            if not empty_nos:
                continue
            rows.append(
                {
                    "file": path.name,
                    "id": q.get("id"),
                    "exam_session": q.get("exam_session", path.stem),
                    "question_number": q.get("question_number"),
                    "subject": q.get("subject"),
                    "exam_type": q.get("exam_type"),
                    "empty_choice_nos": empty_nos,
                    "choice_count": len(q.get("choices") or []),
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-dir",
        type=Path,
        default=DEFAULT_JSON_DIR,
        help="JSON 디렉터리 (기본 assets/jsons)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_JSON_DIR / "empty-choice-text-report.json",
        help="결과 JSON 경로",
    )
    args = parser.parse_args()
    rows = find_empty_choice_text(args.json_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"빈 보기 text 문항: {len(rows)}개")
    for r in rows:
        nos = ", ".join(str(n) for n in r["empty_choice_nos"])
        print(
            f"  {r['exam_session']} | Q{r['question_number']} | {r['subject']} | "
            f"empty no=[{nos}] | {r['id']}"
        )
    print(f"\n저장: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
