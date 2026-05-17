/** GitHub blob 경로 (표시·링크용). trailing slash 없음 */
export const EXAM_GITHUB_BLOB_BASE =
  import.meta.env.VITE_EXAM_JSON_BASE?.toString().trim() ||
  'https://github.com/idlepoe/joonggaego/blob/main';

/** 회독·모의고사 과목 (JSON subject 필드와 동일) */
export const EXAM_SUBJECTS = ['부동산학개론', '민법 및 민사특별법'] as const;

export type ExamSubject = (typeof EXAM_SUBJECTS)[number];

/** GitHub blob URL → raw.githubusercontent.com (fetch용) */
export function githubBlobToRaw(url: string): string {
  return url
    .replace(/^https:\/\/github\.com\//, 'https://raw.githubusercontent.com/')
    .replace('/blob/', '/');
}

/** JSON 연결 링크 (blob 형태) */
export function examJsonUrl(examSession: string): string {
  return `${EXAM_GITHUB_BLOB_BASE}/assets/jsons/${encodeURIComponent(examSession)}.json`;
}

/** JSON fetch URL (raw) */
export function examJsonFetchUrl(examSession: string): string {
  return githubBlobToRaw(examJsonUrl(examSession));
}

export function examSessionsManifestUrl(): string {
  return githubBlobToRaw(`${EXAM_GITHUB_BLOB_BASE}/assets/jsons/exam-sessions.json`);
}

/** 보충 이미지: `{question_id}.png` */
export function examQuestionImageUrl(questionId: string): string {
  return githubBlobToRaw(
    `${EXAM_GITHUB_BLOB_BASE}/assets/images/${encodeURIComponent(questionId)}.png`,
  );
}

/** 보충 이미지: `{question_id}_{choiceNo}.png` */
export function examChoiceImageUrl(questionId: string, choiceNo: number): string {
  return githubBlobToRaw(
    `${EXAM_GITHUB_BLOB_BASE}/assets/images/${encodeURIComponent(questionId)}_${choiceNo}.png`,
  );
}
