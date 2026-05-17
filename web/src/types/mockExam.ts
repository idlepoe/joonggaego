import type { ExamQuestion } from './exam';

export type MockExamState = {
  subject: string;
  questions: ExamQuestion[];
  answers: (number | null)[];
  startedAt: number;
  currentIndex: number;
};

export type MockExamHistoryEntry = {
  subject: string;
  questions: ExamQuestion[];
  answers: (number | null)[];
  /** 시험 시작 시각(채점 저장 시 포함). 구버전 이력에는 없을 수 있음 */
  startedAt?: number;
  endedAt: number;
  correctCount: number;
  isPassed: boolean;
};
