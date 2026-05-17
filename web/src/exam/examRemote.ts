import type { ExamQuestion } from 'src/types/exam';
import { examJsonUrl, examSessionsManifestUrl } from './constants';

export type ExamSessionsManifest = {
  sessions: string[];
};

const jsonCache = new Map<string, Promise<ExamQuestion[]>>();
let sessionsManifestPromise: Promise<ExamSessionsManifest> | null = null;

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'default' });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${url}`);
  }
  return res.json() as Promise<T>;
}

export function fetchExamSessionsManifest(): Promise<ExamSessionsManifest> {
  if (!sessionsManifestPromise) {
    sessionsManifestPromise = fetchJson<ExamSessionsManifest>(examSessionsManifestUrl());
  }
  return sessionsManifestPromise;
}

export function listSessionsFromManifest(manifest: ExamSessionsManifest): string[] {
  return [...manifest.sessions];
}

export function fetchExamJson(examSession: string): Promise<ExamQuestion[]> {
  const key = examSession;
  let p = jsonCache.get(key);
  if (!p) {
    p = fetchJson<ExamQuestion[]>(examJsonUrl(examSession));
    jsonCache.set(key, p);
  }
  return p;
}

export function clearExamJsonCache(): void {
  jsonCache.clear();
  sessionsManifestPromise = null;
}

/** 계획서 명칭과 동일: 원격 회차 JSON → 문항 배열 */
export const loadSessionFromRemote = fetchExamJson;

/** 전 회차에서 해당 과목 문항 풀 (id 중복 제거) */
export async function fetchAllQuestionsForSubject(subject: string): Promise<ExamQuestion[]> {
  const manifest = await fetchExamSessionsManifest();
  const sessions = listSessionsFromManifest(manifest);
  const arrays = await Promise.all(sessions.map((s) => loadSessionFromRemote(s)));
  const flat = arrays.flat().filter((q) => q.subject === subject);
  const byId = new Map<string, ExamQuestion>();
  for (const q of flat) {
    byId.set(q.id, q);
  }
  return [...byId.values()];
}

function shuffleTake(questions: ExamQuestion[], n: number): ExamQuestion[] {
  const copy = [...questions];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const tmp = copy[i]!;
    copy[i] = copy[j]!;
    copy[j] = tmp;
  }
  const take = Math.min(n, copy.length);
  return copy.slice(0, take);
}

/** 모의고사용 최대 40문항 무작위 샘플 */
export async function buildMockExamQuestions(subject: string): Promise<ExamQuestion[]> {
  const pool = await fetchAllQuestionsForSubject(subject);
  return shuffleTake(pool, 40);
}
