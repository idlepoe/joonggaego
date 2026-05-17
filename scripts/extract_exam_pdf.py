"""
Extract 공인중개사 1차 교사용 PDFs to JSON (README schema).

Usage:
  python scripts/extract_exam_pdf.py --input assets/pdfs --output-dir assets/jsons
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import fitz

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from fix_choice_spaces import fix_linebreak_spaces  # noqa: E402

MARK_WHITE = "①②③④⑤"
MARK_NEG = "❶❷❸❹❺"

MARK_TO_NUM: dict[str, int] = {}
for i, ch in enumerate(MARK_WHITE):
    MARK_TO_NUM[ch] = i + 1
for i, ch in enumerate(MARK_NEG):
    MARK_TO_NUM[ch] = i + 1

CHOICE_MARKERS = re.compile("[①②③④⑤❶❷❸❹❺]")
QUESTION_START = re.compile(r"^(\d{1,3})\.\s+(.*)$")
HEADER_PREFIXES = (
    "공인중개사",
    "전자문제집 CBT",
    "최강 자격증 기출문제",
    "◐",
    "◑",
)
FOOTER_PREFIXES = (
    "기출문제 및 해설집",
    "종이 문제집이 아닌",
    "PC 버전 및 어플",
    "오답 및 오탈자",
    "에서 확인하세요",
    "www.comcbt.com",
    "https://",
)
SUBJECT_LINE = re.compile(r"^\s*\d과목\s*:")
FILENAME_DATE = re.compile(
    r"^joonggaego1_(?P<ymd>\d{8})\.pdf$",
    re.IGNORECASE,
)
# 레거시: 공인중개사1차20050522(교사용).pdf
FILENAME_DATE_LEGACY = re.compile(
    r"공인중개사1차(?P<ymd>\d{8})\(교사용\)\.pdf$",
    re.IGNORECASE,
)

SUBJECT_BY_NUMBER: tuple[tuple[int, int, str], ...] = (
    (1, 40, "부동산학개론"),
    (41, 80, "민법 및 민사특별법"),
)

def parse_filename_meta(path: Path) -> tuple[str, str]:
    m = FILENAME_DATE.search(path.name) or FILENAME_DATE_LEGACY.search(path.name)
    if not m:
        raise ValueError(f"Filename not recognized: {path.name}")
    ymd = m.group("ymd")
    session = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:8]}"
    return "공인중개사1차", session


def subject_for_question_number(n: int) -> str:
    for lo, hi, name in SUBJECT_BY_NUMBER:
        if lo <= n <= hi:
            return name
    raise ValueError(f"question_number out of range 1-80: {n}")


def make_question_id(session_compact: str, qn: int) -> str:
    return f"joonggaego1_{session_compact}_{qn}"


def split_choice_segments(line: str) -> list[tuple[str, str]]:
    matches = list(CHOICE_MARKERS.finditer(line))
    if not matches:
        return []
    glyphs = [m.group(0) for m in matches]
    if len(matches) >= 2 and len(set(glyphs)) == 1:
        m0 = matches[0]
        return [(m0.group(0), line[m0.end() :].strip())]

    out: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        marker = m.group(0)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(line)
        body = line[start:end].strip()
        out.append((marker, body))
    return out


def strip_noise_lines(text: str) -> str:
    lines_out: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            lines_out.append("")
            continue
        if SUBJECT_LINE.match(line):
            continue
        if any(s.startswith(p) for p in HEADER_PREFIXES):
            continue
        lines_out.append(line)
    return "\n".join(lines_out)


def split_into_question_blocks(cleaned: str) -> list[str]:
    lines = cleaned.splitlines()
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and QUESTION_START.match(stripped):
            if current:
                blocks.append("\n".join(current))
            current = [line]
        else:
            if current:
                current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def is_footer_line(line: str) -> bool:
    s = line.strip()
    return any(s.startswith(p) for p in FOOTER_PREFIXES)


def parse_question_block(
    block: str, exam_type: str, session: str, session_compact: str
) -> dict | None:
    lines = block.splitlines()
    if not lines:
        return None
    first = lines[0].strip()
    m = QUESTION_START.match(first)
    if not m:
        return None
    qn = int(m.group(1))
    stem_buf: list[str] = [m.group(2).strip()] if m.group(2).strip() else []
    choices: list[dict] = []

    for raw in lines[1:]:
        line = raw.strip()
        if not line:
            continue
        segments = split_choice_segments(line)
        if segments:
            if len(choices) >= 5:
                break
            for marker, body in segments:
                if len(choices) >= 5:
                    break
                is_correct = marker in MARK_NEG
                num = MARK_TO_NUM[marker]
                choices.append({"no": num, "text": body, "_correct": is_correct})
        else:
            if choices:
                if len(choices) >= 5 and is_footer_line(line):
                    break
                choices[-1]["text"] = (choices[-1]["text"] + " " + line).strip()
            else:
                stem_buf.append(line)

    stem = " ".join(x for x in stem_buf if x).strip()
    if not stem or len(choices) != 5:
        return None

    correct = [c["no"] for c in choices if c.get("_correct")]
    if not correct:
        return None
    correct_no = correct[0]

    choices_out = [
        {
            "no": c["no"],
            "text": fix_linebreak_spaces(c["text"]),
        }
        for c in sorted(choices, key=lambda x: x["no"])
    ]

    return {
        "id": make_question_id(session_compact, qn),
        "exam_type": exam_type,
        "exam_session": session,
        "subject": subject_for_question_number(qn),
        "question_number": qn,
        "question_text": fix_linebreak_spaces(stem),
        "choices": choices_out,
        "correct_answer": correct_no,
    }


def pdf_to_raw_text(path: Path) -> str:
    doc = fitz.open(path)
    try:
        return "\n".join(doc[i].get_text() for i in range(len(doc)))
    finally:
        doc.close()


def extract_questions_from_text(
    raw: str,
    exam_type: str,
    session: str,
    session_compact: str,
) -> list[dict]:
    cleaned = strip_noise_lines(raw)
    blocks = split_into_question_blocks(cleaned)
    by_number: dict[int, dict] = {}
    for b in blocks:
        q = parse_question_block(b, exam_type, session, session_compact)
        if q:
            by_number[q["question_number"]] = q
    return [by_number[n] for n in sorted(by_number) if 1 <= n <= 80]


def extract_pdf(path: Path) -> list[dict]:
    exam_type, session = parse_filename_meta(path)
    ymd = session.replace("-", "")
    raw = pdf_to_raw_text(path)
    return extract_questions_from_text(raw, exam_type, session, ymd)


def collect_pdf_paths(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if not input_path.is_dir():
        raise FileNotFoundError(str(input_path))
    paths = sorted(
        p
        for p in input_path.iterdir()
        if p.suffix.lower() == ".pdf"
        and (
            FILENAME_DATE.match(p.name)
            or FILENAME_DATE_LEGACY.search(p.name)
        )
    )
    if not paths:
        raise FileNotFoundError(f"No matching PDFs under {input_path}")
    return paths


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description="Extract exam questions from 교사용 PDFs to JSON.")
    ap.add_argument("--input", type=Path, default=root / "assets" / "pdfs")
    ap.add_argument("--output-dir", type=Path, default=root / "assets" / "jsons")
    ap.add_argument("--dump-text", type=Path)
    args = ap.parse_args()

    paths = collect_pdf_paths(args.input)
    if args.dump_text:
        args.dump_text.parent.mkdir(parents=True, exist_ok=True)
        args.dump_text.write_text(pdf_to_raw_text(paths[0]), encoding="utf-8")
        print(f"Wrote raw text dump: {args.dump_text}", file=sys.stderr)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for p in paths:
        try:
            qs = extract_pdf(p)
        except ValueError as e:
            print(f"Skip {p.name}: {e}", file=sys.stderr)
            continue

        _, session = parse_filename_meta(p)
        out_path = args.output_dir / f"{session}.json"
        out_path.write_text(json.dumps(qs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written += 1
        nums = [q["question_number"] for q in qs]
        print(
            f"{p.name}: {len(qs)} questions ({min(nums)}–{max(nums)}) -> {out_path.name}",
            file=sys.stderr,
        )
        if len(qs) != 80:
            print(f"  WARNING: expected 80, got {len(qs)}", file=sys.stderr)

    print(f"Wrote {written} JSON file(s) under {args.output_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
