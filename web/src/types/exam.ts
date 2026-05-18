export type ExamChoice = {
  no: number;
  text: string;
};

export type ExamAiExplanation = {
  correctExplanation: string;
  wrongAnswerNotes: string[];
  examTip: string;
};

export type ExamQuestion = {
  id: string;
  exam_type: string;
  exam_session: string;
  subject: string;
  question_number: number;
  question_text: string;
  choices: ExamChoice[];
  correct_answer: number;
  aiExplanation?: ExamAiExplanation;
};

/** 화면에 표시할 만큼 aiExplanation 필드가 채워져 있는지 */
export function hasDisplayableAiExplanation(
  explanation: ExamAiExplanation | null | undefined,
): boolean {
  if (!explanation) return false;
  if (explanation.correctExplanation?.trim()) return true;
  if (explanation.examTip?.trim()) return true;
  return (
    Array.isArray(explanation.wrongAnswerNotes) &&
    explanation.wrongAnswerNotes.some((n) => typeof n === 'string' && n.trim())
  );
}
