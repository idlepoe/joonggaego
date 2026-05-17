"""웹 `src/exam/constants.ts`와 동일한 보충 이미지 URL 후보 (GitHub raw).

파일이 없을 수 있다. 웹은 로드 실패 시 숨기고, Gemini 스크립트는 HEAD/GET으로
존재할 때만 URL 필드·첨부를 사용한다.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_GITHUB_BLOB_BASE = "https://github.com/idlepoe/joonggaego/blob/main"


def exam_github_blob_base() -> str:
    return os.getenv("EXAM_JSON_BASE", DEFAULT_GITHUB_BLOB_BASE).strip().rstrip("/")


def github_blob_to_raw(url: str) -> str:
    return (
        url.replace("https://github.com/", "https://raw.githubusercontent.com/")
        .replace("/blob/", "/")
    )


def exam_question_image_url(question_id: str) -> str:
    """AnswerSheet: examQuestionImageUrl(id) → assets/images/{id}.png"""
    qid = quote(str(question_id), safe="")
    return github_blob_to_raw(f"{exam_github_blob_base()}/assets/images/{qid}.png")


def exam_choice_image_url(question_id: str, choice_no: int) -> str:
    """AnswerSheet: examChoiceImageUrl(id, no) → assets/images/{id}_{no}.png"""
    qid = quote(str(question_id), safe="")
    return github_blob_to_raw(f"{exam_github_blob_base()}/assets/images/{qid}_{int(choice_no)}.png")
