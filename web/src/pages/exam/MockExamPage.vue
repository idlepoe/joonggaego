<template>
  <q-page padding class="q-pb-xl">
    <q-inner-loading :showing="loading" color="primary" />

    <template v-if="!loading && current">
      <div class="q-mb-lg" :class="questionTextClass" style="white-space: pre-wrap">
        {{ displayIndex }}. {{ current.question_text }}
      </div>
      <ExamOptionalRemoteImage :src="examQuestionImageUrl(current.id)" />
      <div class="column q-gutter-sm q-mb-lg">
        <q-card
          v-for="c in current.choices"
          :key="c.no"
          flat
          bordered
          class="q-pa-md cursor-pointer"
          :class="choiceCardClass(c.no)"
          @click="pickChoice(c.no)"
        >
          <div :class="choiceTextClass">
            <span class="text-weight-bold">{{ c.no }}.</span>
            {{ c.text }}
          </div>
          <ExamOptionalRemoteImage :src="examChoiceImageUrl(current.id, c.no)" />
        </q-card>
      </div>
    </template>

    <div v-else-if="!loading && !loadError && questions.length === 0" class="text-grey">
      모의고사 문항을 만들 수 없습니다.
    </div>
    <div v-if="loadError" class="text-negative">{{ loadError }}</div>

    <q-dialog v-model="answerReviewOpen" class="mock-answer-review-dialog">
      <q-card class="mock-answer-review-card">
        <q-card-section class="row items-center q-pb-none no-wrap q-px-sm">
          <div class="text-h6">답안 확인</div>
          <q-space />
          <q-btn v-close-popup flat round dense icon="close" aria-label="닫기" />
        </q-card-section>
        <q-card-section class="q-pt-sm q-px-sm mock-answer-review-scroll">
          <q-markup-table flat bordered dense separator="cell" class="mock-review-markup-table">
            <thead>
              <tr>
                <th class="text-center text-weight-medium mock-review-th-idx">#</th>
                <th class="text-left text-weight-medium mock-review-th-q">문제</th>
                <th class="text-right text-weight-medium mock-review-th-a">답안</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in answerReviewRows"
                :key="row.index"
                class="cursor-pointer"
                @click="goToReviewIndex(row.index)"
              >
                <td class="mock-review-td-idx text-center">{{ row.index + 1 }}</td>
                <td class="mock-review-td-q">{{ row.questionPreview }}</td>
                <td class="mock-review-td-a text-right">{{ row.answerText }}</td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-page-sticky
      v-if="!loading && questions.length > 0"
      class="exam-sheet-nav-sticky-wrap"
      position="bottom"
      expand
    >
      <ExamSheetNavToolbar
        :prev-disabled="currentIndex <= 0"
        :next-disabled="false"
        @prev="prev"
        @next="next"
      />
    </q-page-sticky>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, watchEffect } from 'vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import type { ExamQuestion } from 'src/types/exam';
import { buildMockExamQuestions } from 'src/exam/examRemote';
import {
  appendMockHistory,
  clearCurrentMockExam,
  readCurrentMockExam,
  writeCurrentMockExam,
} from 'src/exam/mockExamStorage';
import { useMockExamToolbarStore } from 'stores/mock-exam-toolbar';
import { useExamUserOptionsStore } from 'stores/exam-user-options';
import MockExamUnfinishedDialog from 'src/components/exam/MockExamUnfinishedDialog.vue';
import ExamOptionalRemoteImage from 'src/components/exam/ExamOptionalRemoteImage.vue';
import ExamSheetNavToolbar from 'src/components/exam/ExamSheetNavToolbar.vue';
import { examChoiceImageUrl, examQuestionImageUrl } from 'src/exam/constants';

const props = defineProps<{
  subject: string;
}>();

const router = useRouter();
const $q = useQuasar();
const mockToolbar = useMockExamToolbarStore();
const examUserOpts = useExamUserOptionsStore();
const { questionTextSize } = storeToRefs(examUserOpts);

const questionTextClass = computed(
  () => `text-body1 exam-question-text--${questionTextSize.value}`,
);

const choiceTextClass = computed(() => `text-body2 exam-question-text--${questionTextSize.value}`);

const loading = ref(true);
const loadError = ref('');
const questions = ref<ExamQuestion[]>([]);
const answers = ref<(number | null)[]>([]);
const startedAt = ref(0);
const currentIndex = ref(0);
const pendingChoice = ref<number | null>(null);
const pendingAdvance = ref(false);

let advanceTimer: number | null = null;
let wallTimer: number | null = null;
let lastSubmitNonce = 0;
let lastReviewNonce = 0;

const answerReviewOpen = ref(false);

function formatAnswerCell(_q: ExamQuestion, ans: number | null): string {
  if (ans == null) return '미작성';
  return String(ans);
}

const answerReviewRows = computed(() =>
  questions.value.map((q, i) => {
    const line = (q.question_text.split(/\r?\n/)[0] ?? '').replace(/\s+/g, ' ').trim();
    return {
      index: i,
      questionPreview: line,
      answerText: formatAnswerCell(q, answers.value[i] ?? null),
    };
  }),
);

const current = computed(() => questions.value[currentIndex.value] ?? null);
const total = computed(() => questions.value.length);
const displayIndex = computed(() => (total.value ? currentIndex.value + 1 : 0));

const toolbarStatusLines = computed(() => {
  if (loading.value) return { line1: '', line2: '' };
  const c = current.value;
  if (!c || total.value === 0) return { line1: '', line2: '' };
  return {
    line1: `${c.exam_type} ${c.subject}`,
    line2: `${displayIndex.value}(현재문항)/${total.value}(총문항)`,
  };
});

watch(
  toolbarStatusLines,
  ({ line1, line2 }) => {
    mockToolbar.setMockToolbarLines(line1, line2);
  },
  { immediate: true },
);

function choiceCardClass(no: number): string | Record<string, boolean> {
  const sel = answers.value[currentIndex.value];
  if (pendingChoice.value === no) return 'exam-mock-choice-pending';
  if (sel === no) return 'exam-mock-choice-selected';
  return '';
}

function updateTimerLabel() {
  const n = questions.value.length;
  if (!n || !startedAt.value) {
    mockToolbar.setTimerLabel('');
    return;
  }
  const elapsed = Math.max(0, Date.now() - startedAt.value);
  const m = Math.floor(elapsed / 60_000);
  const s = Math.floor((elapsed % 60_000) / 1000);
  mockToolbar.setTimerLabel(`${m}:${String(s).padStart(2, '0')} / ${n}분`);
}

function getUnansweredIndices(): number[] {
  const out: number[] = [];
  for (let i = 0; i < answers.value.length; i++) {
    if (answers.value[i] == null) out.push(i);
  }
  return out;
}

function scoreExam(): { correctCount: number; isPassed: boolean } {
  let correct = 0;
  for (let i = 0; i < questions.value.length; i++) {
    const a = answers.value[i];
    if (a != null && questions.value[i]!.correct_answer === a) correct++;
  }
  const total = questions.value.length;
  const need = Math.ceil(total * 0.6);
  return { correctCount: correct, isPassed: correct >= need };
}

function showScoreAndFinish() {
  const { correctCount, isPassed } = scoreExam();
  const total = questions.value.length;
  $q.dialog({
    title: '채점 결과',
    message: `${isPassed ? '합격' : '불합격'}\n정답: ${correctCount} / ${total}`,
    persistent: true,
    ok: {
      label: '확인',
      color: 'primary',
      noCaps: true,
    },
  }).onOk(() => {
    appendMockHistory({
      subject: props.subject,
      questions: [...questions.value],
      answers: [...answers.value],
      startedAt: startedAt.value,
      endedAt: Date.now(),
      correctCount,
      isPassed,
    });
    clearCurrentMockExam();
    mockToolbar.clearToolbar();
    void router.push({ name: 'exam-main' });
  });
}

function openExamEndDialogs() {
  if (!questions.value.length) return;
  const unanswered = getUnansweredIndices();
  if (unanswered.length > 0) {
    $q.dialog({
      component: MockExamUnfinishedDialog,
      componentProps: {
        onYes: () => {
          currentIndex.value = unanswered[0]!;
        },
        onScore: () => {
          showScoreAndFinish();
        },
      },
    });
  } else {
    $q.dialog({
      title: '안내',
      message: '답안을 제출하시겠습니까?',
      persistent: true,
      ok: {
        label: '확인',
        color: 'primary',
        noCaps: true,
      },
      cancel: {
        label: '취소',
        flat: true,
        noCaps: true,
      },
    }).onOk(() => {
      showScoreAndFinish();
    });
  }
}

function pickChoice(no: number) {
  if (pendingAdvance.value || loading.value) return;
  pendingChoice.value = no;
  pendingAdvance.value = true;
  if (advanceTimer) window.clearTimeout(advanceTimer);
  advanceTimer = window.setTimeout(() => {
    advanceTimer = null;
    answers.value[currentIndex.value] = no;
    pendingChoice.value = null;
    pendingAdvance.value = false;
    const last = currentIndex.value >= questions.value.length - 1;
    if (last) {
      openExamEndDialogs();
    } else {
      currentIndex.value++;
    }
  }, 500);
}

function goToReviewIndex(i: number) {
  if (advanceTimer != null) {
    window.clearTimeout(advanceTimer);
    advanceTimer = null;
  }
  pendingChoice.value = null;
  pendingAdvance.value = false;
  const max = Math.max(0, questions.value.length - 1);
  currentIndex.value = Math.min(Math.max(0, i), max);
  answerReviewOpen.value = false;
  updateTimerLabel();
}

function prev() {
  if (currentIndex.value > 0) currentIndex.value--;
}

function next() {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++;
    return;
  }
  openExamEndDialogs();
}

watchEffect(() => {
  const qs = questions.value;
  const as = answers.value;
  const ix = currentIndex.value;
  const st = startedAt.value;
  if (!qs.length || !st) return;
  writeCurrentMockExam({
    subject: props.subject,
    questions: qs,
    answers: [...as],
    startedAt: st,
    currentIndex: ix,
  });
});

watch(
  () => mockToolbar.submitNonce,
  (n) => {
    if (n <= lastSubmitNonce) return;
    lastSubmitNonce = n;
    if (!questions.value.length || loading.value) return;
    openExamEndDialogs();
  },
);

watch(
  () => mockToolbar.reviewNonce,
  (n) => {
    if (n <= lastReviewNonce) return;
    lastReviewNonce = n;
    if (!questions.value.length || loading.value) return;
    answerReviewOpen.value = true;
  },
);

onMounted(async () => {
  mockToolbar.clearToolbar();
  lastSubmitNonce = mockToolbar.submitNonce;
  lastReviewNonce = mockToolbar.reviewNonce;
  loading.value = true;
  loadError.value = '';
  try {
    const saved = readCurrentMockExam();
    if (saved && saved.subject === props.subject && saved.questions?.length) {
      questions.value = saved.questions;
      answers.value =
        saved.answers.length === saved.questions.length
          ? [...saved.answers]
          : saved.questions.map(() => null);
      startedAt.value = saved.startedAt;
      currentIndex.value = Math.min(Math.max(0, saved.currentIndex), saved.questions.length - 1);
    } else {
      if (saved) clearCurrentMockExam();
      const q = await buildMockExamQuestions(props.subject);
      if (!q.length) {
        loadError.value = '해당 과목 문항이 없습니다.';
        return;
      }
      questions.value = q;
      answers.value = q.map(() => null);
      startedAt.value = Date.now();
      currentIndex.value = 0;
    }
    wallTimer = window.setInterval(updateTimerLabel, 250);
    updateTimerLabel();
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    loadError.value = `문항을 불러오지 못했습니다: ${msg}`;
    $q.notify({ type: 'negative', message: loadError.value });
  } finally {
    loading.value = false;
  }
});

onUnmounted(() => {
  if (advanceTimer) window.clearTimeout(advanceTimer);
  if (wallTimer != null) window.clearInterval(wallTimer);
  mockToolbar.clearToolbar();
});
</script>

<style scoped>
.mock-answer-review-dialog :deep(.q-dialog__inner) {
  max-width: 100%;
  overflow-x: hidden;
  padding-left: 8px;
  padding-right: 8px;
  box-sizing: border-box;
}
.mock-answer-review-card {
  width: min(560px, 92vw);
  max-width: min(560px, 100%);
  max-height: min(72vh, 520px);
  overflow-x: hidden;
  box-sizing: border-box;
}
.mock-answer-review-scroll {
  overflow-x: hidden;
  overflow-y: auto;
  max-height: min(52vh, 400px);
  max-width: 100%;
  min-width: 0;
}
.mock-review-markup-table {
  display: block;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  overflow-x: hidden;
  box-sizing: border-box;
}
.mock-review-markup-table :deep(table) {
  width: 100%;
  max-width: 100%;
  table-layout: fixed;
}
.mock-review-markup-table :deep(thead th),
.mock-review-markup-table :deep(tbody td) {
  overflow: hidden;
  vertical-align: middle;
}
.mock-review-th-idx,
.mock-review-td-idx {
  width: 2.5rem;
  min-width: 2.5rem;
  max-width: 2.5rem;
  white-space: nowrap;
  font-size: 0.8125rem;
}
.mock-review-th-q,
.mock-review-td-q {
  width: auto;
  max-width: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.8125rem;
}
.mock-review-th-a,
.mock-review-td-a {
  width: 4.75rem;
  min-width: 4.75rem;
  max-width: 4.75rem;
  white-space: nowrap;
  font-size: 0.8125rem;
}
</style>
