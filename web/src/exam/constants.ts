/** GitHub Raw 루트 (trailing slash 없음). blob URL 사용 금지. */
export const EXAM_RAW_REPO_BASE =
  import.meta.env.VITE_EXAM_RAW_BASE?.toString().trim() ||
  'https://raw.githubusercontent.com/idlepoe/jootaek_exam/main';

export function examJsonUrl(examSession: string): string {
  return `${EXAM_RAW_REPO_BASE}/assets/jsons/${encodeURIComponent(examSession)}.json`;
}

export function examSessionsManifestUrl(): string {
  return `${EXAM_RAW_REPO_BASE}/assets/jsons/exam-sessions.json`;
}

/** 보충 이미지: `{question_id}.png` (GitHub Raw 동일 베이스) */
export function examQuestionImageUrl(questionId: string): string {
  return `${EXAM_RAW_REPO_BASE}/assets/images/${encodeURIComponent(questionId)}.png`;
}

/** 보충 이미지: `{question_id}_{choiceNo}.png` */
export function examChoiceImageUrl(questionId: string, choiceNo: number): string {
  return `${EXAM_RAW_REPO_BASE}/assets/images/${encodeURIComponent(questionId)}_${choiceNo}.png`;
}
