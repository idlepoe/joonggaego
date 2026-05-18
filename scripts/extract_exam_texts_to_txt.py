"""assets/jsons 시험 JSON에서 question_text·choices.text만 한 txt에 추출."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def iter_texts(questions: list[dict]) -> list[str]:
    lines: list[str] = []
    for q in questions:
        stem = q.get("question_text")
        if isinstance(stem, str) and stem:
            lines.append(stem)
        for c in q.get("choices") or []:
            text = c.get("text")
            if isinstance(text, str) and text:
                lines.append(text)
    return lines


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-dir",
        type=Path,
        default=root / "assets" / "jsons",
        help="입력 JSON 디렉터리 (기본: assets/jsons)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="출력 txt 경로 (기본: <json-dir>/exam-texts.txt)",
    )
    args = parser.parse_args()
    json_dir: Path = args.json_dir
    out_path: Path = args.out if args.out is not None else json_dir / "exam-texts.txt"

    if not json_dir.is_dir():
        print(f"JSON directory not found: {json_dir}", file=sys.stderr)
        return 1

    all_lines: list[str] = []
    file_count = 0
    question_count = 0

    for json_path in sorted(json_dir.glob("*.json")):
        if json_path.name == "exam-sessions.json":
            continue
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"SKIP {json_path.name}: {e}", file=sys.stderr)
            continue
        if not isinstance(data, list):
            print(f"SKIP {json_path.name}: expected a JSON array", file=sys.stderr)
            continue
        all_lines.extend(iter_texts(data))
        file_count += 1
        question_count += len(data)
        print(f"{json_path.name} ({len(data)} questions)")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(all_lines) + ("\n" if all_lines else ""), encoding="utf-8")
    print(
        f"Done. {file_count} json files, {question_count} questions, "
        f"{len(all_lines)} lines -> {out_path.relative_to(root)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
