import { Dark } from 'quasar';

export const EXAM_USER_OPTIONS_LS_KEY = 'jootaek_exam:user_options';

export type ExamThemeMode = 'system' | 'light' | 'dark';
export type StickyButtonHeight = 'normal' | 'large' | 'xlarge';
export type QuestionTextSize = 'sm' | 'md' | 'lg' | 'xl' | 'max';
export type StickyButtonOrder = 'prev-next' | 'next-prev';

export interface ExamUserOptions {
  themeMode: ExamThemeMode;
  correctHighlightHex: string;
  /** 정답 하이라이트 영역 글자 색 */
  correctHighlightTextHex: string;
  /** 모의고사 풀이 시 선택한 보기 카드 배경(pickChoice) */
  pickChoiceHighlightHex: string;
  /** 모의고사 풀이 시 선택한 보기 카드 글자 색 */
  pickChoiceHighlightTextHex: string;
  stickyButtonHeight: StickyButtonHeight;
  questionTextSize: QuestionTextSize;
  stickyButtonOrder: StickyButtonOrder;
}

export const DEFAULT_EXAM_USER_OPTIONS: ExamUserOptions = {
  themeMode: 'system',
  correctHighlightHex: '#ffcccc',
  correctHighlightTextHex: '#ffffff',
  pickChoiceHighlightHex: '#1565c0',
  pickChoiceHighlightTextHex: '#ffffff',
  stickyButtonHeight: 'normal',
  questionTextSize: 'md',
  stickyButtonOrder: 'prev-next',
};

const THEME_MODES: ExamThemeMode[] = ['system', 'light', 'dark'];
const STICKY_HEIGHTS: StickyButtonHeight[] = ['normal', 'large', 'xlarge'];
const TEXT_SIZES: QuestionTextSize[] = ['sm', 'md', 'lg', 'xl', 'max'];
const BUTTON_ORDERS: StickyButtonOrder[] = ['prev-next', 'next-prev'];

const HEX_RE = /^#[0-9A-Fa-f]{6}$/;

function isValidHex(s: string): boolean {
  return HEX_RE.test(s);
}

function coerceThemeMode(v: unknown): ExamThemeMode {
  return typeof v === 'string' && (THEME_MODES as readonly string[]).includes(v)
    ? (v as ExamThemeMode)
    : DEFAULT_EXAM_USER_OPTIONS.themeMode;
}

function coerceStickyHeight(v: unknown): StickyButtonHeight {
  return typeof v === 'string' && (STICKY_HEIGHTS as readonly string[]).includes(v)
    ? (v as StickyButtonHeight)
    : DEFAULT_EXAM_USER_OPTIONS.stickyButtonHeight;
}

function coerceTextSize(v: unknown): QuestionTextSize {
  return typeof v === 'string' && (TEXT_SIZES as readonly string[]).includes(v)
    ? (v as QuestionTextSize)
    : DEFAULT_EXAM_USER_OPTIONS.questionTextSize;
}

function coerceButtonOrder(v: unknown): StickyButtonOrder {
  return typeof v === 'string' && (BUTTON_ORDERS as readonly string[]).includes(v)
    ? (v as StickyButtonOrder)
    : DEFAULT_EXAM_USER_OPTIONS.stickyButtonOrder;
}

function coerceCorrectHex(v: unknown): string {
  return typeof v === 'string' && isValidHex(v) ? v : DEFAULT_EXAM_USER_OPTIONS.correctHighlightHex;
}

function coerceCorrectTextHex(v: unknown): string {
  return typeof v === 'string' && isValidHex(v)
    ? v
    : DEFAULT_EXAM_USER_OPTIONS.correctHighlightTextHex;
}

function coercePickHex(v: unknown): string {
  return typeof v === 'string' && isValidHex(v)
    ? v
    : DEFAULT_EXAM_USER_OPTIONS.pickChoiceHighlightHex;
}

function coercePickTextHex(v: unknown): string {
  return typeof v === 'string' && isValidHex(v)
    ? v
    : DEFAULT_EXAM_USER_OPTIONS.pickChoiceHighlightTextHex;
}

/** LS 및 부분 객체를 기본값과 병합해 정규화합니다. */
export function normalizeExamUserOptions(
  partial: Partial<ExamUserOptions> | null | undefined,
): ExamUserOptions {
  const p = partial ?? {};
  return {
    themeMode: coerceThemeMode(p.themeMode),
    correctHighlightHex: coerceCorrectHex(p.correctHighlightHex),
    correctHighlightTextHex: coerceCorrectTextHex(p.correctHighlightTextHex),
    pickChoiceHighlightHex: coercePickHex(p.pickChoiceHighlightHex),
    pickChoiceHighlightTextHex: coercePickTextHex(p.pickChoiceHighlightTextHex),
    stickyButtonHeight: coerceStickyHeight(p.stickyButtonHeight),
    questionTextSize: coerceTextSize(p.questionTextSize),
    stickyButtonOrder: coerceButtonOrder(p.stickyButtonOrder),
  };
}

export function readExamUserOptions(): ExamUserOptions {
  if (typeof localStorage === 'undefined') {
    return { ...DEFAULT_EXAM_USER_OPTIONS };
  }
  try {
    const raw = localStorage.getItem(EXAM_USER_OPTIONS_LS_KEY);
    if (raw == null || raw === '') {
      return { ...DEFAULT_EXAM_USER_OPTIONS };
    }
    const parsed = JSON.parse(raw) as unknown;
    if (parsed == null || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return { ...DEFAULT_EXAM_USER_OPTIONS };
    }
    return normalizeExamUserOptions(parsed as Partial<ExamUserOptions>);
  } catch {
    return { ...DEFAULT_EXAM_USER_OPTIONS };
  }
}

export function writeExamUserOptions(opts: ExamUserOptions): void {
  if (typeof localStorage === 'undefined') return;
  try {
    localStorage.setItem(EXAM_USER_OPTIONS_LS_KEY, JSON.stringify(opts));
  } catch {
    // ignore quota / private mode
  }
}

export function mergeExamUserOptionsPatch(
  current: ExamUserOptions,
  patch: Partial<ExamUserOptions>,
): ExamUserOptions {
  return normalizeExamUserOptions({ ...current, ...patch });
}

/** 테마·정답 하이라이트 CSS 변수를 DOM에 반영합니다. */
export function syncExamUserOptionsToDom(opts: ExamUserOptions): void {
  if (opts.themeMode === 'light') {
    Dark.set(false);
  } else if (opts.themeMode === 'dark') {
    Dark.set(true);
  } else {
    Dark.set('auto');
  }

  const root = typeof document !== 'undefined' ? document.documentElement : null;
  if (root) {
    root.style.setProperty('--exam-correct-bg', opts.correctHighlightHex);
    root.style.setProperty('--exam-correct-text', opts.correctHighlightTextHex);
    root.style.setProperty('--exam-pick-choice-bg', opts.pickChoiceHighlightHex);
    root.style.setProperty('--exam-pick-choice-text', opts.pickChoiceHighlightTextHex);
  }
}
