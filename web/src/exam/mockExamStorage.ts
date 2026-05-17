import type { MockExamHistoryEntry, MockExamState } from 'src/types/mockExam';

const KEY_CURRENT = 'jootaek_exam:current_mock_exam';
const KEY_HISTORY = 'jootaek_exam:mock_exam_history';

export function readCurrentMockExam(): MockExamState | null {
  try {
    const raw = localStorage.getItem(KEY_CURRENT);
    if (!raw) return null;
    return JSON.parse(raw) as MockExamState;
  } catch {
    return null;
  }
}

export function writeCurrentMockExam(state: MockExamState): void {
  localStorage.setItem(KEY_CURRENT, JSON.stringify(state));
}

export function clearCurrentMockExam(): void {
  localStorage.removeItem(KEY_CURRENT);
}

export function readMockHistory(): MockExamHistoryEntry[] {
  try {
    const raw = localStorage.getItem(KEY_HISTORY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? (parsed as MockExamHistoryEntry[]) : [];
  } catch {
    return [];
  }
}

export function appendMockHistory(entry: MockExamHistoryEntry): void {
  const list = readMockHistory();
  list.push(entry);
  localStorage.setItem(KEY_HISTORY, JSON.stringify(list));
}

export function clearMockHistory(): void {
  localStorage.removeItem(KEY_HISTORY);
}
