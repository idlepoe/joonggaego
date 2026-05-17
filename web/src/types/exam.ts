export type ExamChoice = {
  no: number;
  text: string;
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
};
