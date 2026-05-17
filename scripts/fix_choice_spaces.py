"""문항 지문·보기 텍스트에서 PDF 줄바꿈으로 생긴 불필요한 공백 제거."""

from __future__ import annotations

import json
import re
from pathlib import Path

# 줄바꿈 뒤 떨어진 조사·어미 앞 공백 제거
_JOSA = "은는이가을를에의도만까지부터와과로다한"
# 조사 뒤에 단어가 바로 이어지면(가장, 가능 등) 공백 제거하지 않음
_RE_JOSA_SPACE = re.compile(
    rf"(?<=[가-힣])\s+(?=[{_JOSA}](?:\s|[,.?!)\]」』]|$|[^\uac00-\ud7a3]))"
)

# 한 글자 뒤 공백 병합 시 붙이지 않을 조사·어미 음절
_JOSA_SYLLABLE = frozenset("을를은는이가에의도와과로고서며면다한히게라중")

# 줄바꿈이 아닌 정상 단어 경계(다음 음절이 새 단어 시작)
_NO_MERGE_ONE_SECOND = frozenset("적가불가능명실동")

# 긴 단어 뒤 한 글자 병합 시 유지할 접속·지시어
_KEEP_SINGLE_AFTER_SPACE = frozenset(
    "및 또는 그 이 한 때 위 중 외 내 각 모든 것 수 점 시 전 후 상 하 간 측".split()
)

# 단어 중간 줄바꿈: "전 면매수" → "전면" + "매수" (한 음절만 병합)
_RE_ONE_TO_ONE = re.compile(
    r"(?<![하되고며면아어여])([가-힣])\s+([가-힣])(?=[가-힣]{2,})"
)
# 형용사·명사 어간 + 하다 활용: "적절 하지", "합의 하였"
_RE_HA_VERB = re.compile(r"([\uac00-\ud7a3]{2,})\s+하(?=여|였|지|고|면|는|옴|음|기)")
_RE_MULTI_TO_ONE = re.compile(
    r"([\uac00-\ud7a3]{2,})\s+([\uac00-\ud7a3])(?=(?:등|과|와|으로|에서)|\s|[^\uac00-\ud7a3]|$)"
)


def fix_linebreak_spaces(text: str) -> str:
    """PDF 줄바꿈 병합 시 생긴 공백만 제거 (정상 띄어쓰기는 유지)."""
    s = _RE_JOSA_SPACE.sub("", text)
    s = _RE_HA_VERB.sub(r"\1하", s)

    def _merge_one(m: re.Match[str]) -> str:
        if m.group(1) in _JOSA_SYLLABLE or m.group(2) in _NO_MERGE_ONE_SECOND:
            return m.group(0)
        return m.group(1) + m.group(2)

    s = _RE_ONE_TO_ONE.sub(_merge_one, s)

    def _merge_end(m: re.Match[str]) -> str:
        single = m.group(2)
        if single in _KEEP_SINGLE_AFTER_SPACE:
            return m.group(0)
        return m.group(1) + m.group(2)

    s = _RE_MULTI_TO_ONE.sub(_merge_end, s)
    return s


# 하위 호환
fix_choice_linebreak_spaces = fix_linebreak_spaces


def fix_questions(questions: list[dict]) -> tuple[int, int]:
    """(보기 수정 수, 지문 수정 수) 반환."""
    choices_changed = 0
    stems_changed = 0
    for q in questions:
        old_stem = q.get("question_text", "")
        new_stem = fix_linebreak_spaces(old_stem)
        if new_stem != old_stem:
            q["question_text"] = new_stem
            stems_changed += 1

        for c in q.get("choices", []):
            old = c.get("text", "")
            new = fix_linebreak_spaces(old)
            if new != old:
                c["text"] = new
                choices_changed += 1
    return choices_changed, stems_changed


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    json_dir = root / "assets" / "jsons"
    total_choices = 0
    total_stems = 0
    for path in sorted(json_dir.glob("*.json")):
        if path.name == "exam-sessions.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        n_choices, n_stems = fix_questions(data)
        if n_choices or n_stems:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{path.name}: {n_stems} stems, {n_choices} choices updated")
            total_choices += n_choices
            total_stems += n_stems
    print(f"Done. {total_stems} question texts, {total_choices} choice texts updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
