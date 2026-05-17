const LS_PREFIX = 'jootaek_exam:qidx:';
const LS_REPEAT_PREFIX = 'jootaek_exam:repeat:';

export function examProgressKey(subject: string, examSession: string): string {
  return `${LS_PREFIX}${subject}:${examSession}`;
}

export function examRepeatCountKey(subject: string, examSession: string): string {
  return `${LS_REPEAT_PREFIX}${subject}:${examSession}`;
}

/** 회독 완료(목록 복귀 확인) 횟수, 없으면 0 */
export function readRepeatCount(subject: string, examSession: string): number {
  const raw = localStorage.getItem(examRepeatCountKey(subject, examSession));
  const n = raw === null ? 0 : Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 0) return 0;
  return n;
}

/** repeat_count 1 증가 후 저장된 값 반환 */
export function incrementRepeatCount(subject: string, examSession: string): number {
  const next = readRepeatCount(subject, examSession) + 1;
  localStorage.setItem(examRepeatCountKey(subject, examSession), String(next));
  return next;
}

/** 문항 진행 인덱스 제거(재진입 시 처음부터) */
export function resetExamProgress(subject: string, examSession: string): void {
  localStorage.removeItem(examProgressKey(subject, examSession));
}

/** 0-based index, clamped to [0, len-1] */
export function readExamProgress(subject: string, examSession: string, length: number): number {
  if (length <= 0) return 0;
  const raw = localStorage.getItem(examProgressKey(subject, examSession));
  const n = raw === null ? 0 : Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 0) return 0;
  return Math.min(n, length - 1);
}

export function writeExamProgress(subject: string, examSession: string, index: number): void {
  localStorage.setItem(examProgressKey(subject, examSession), String(index));
}

/** `examProgressKey` / `examRepeatCountKey` 패턴의 모든 항목 제거(전 과목·전 회차) */
export function clearAllExamProgressAndRepeat(): void {
  const keysToRemove: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (!k) continue;
    if (k.startsWith(LS_PREFIX) || k.startsWith(LS_REPEAT_PREFIX)) {
      keysToRemove.push(k);
    }
  }
  for (const k of keysToRemove) {
    localStorage.removeItem(k);
  }
}
