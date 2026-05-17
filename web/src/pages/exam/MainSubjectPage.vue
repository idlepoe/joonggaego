<template>
  <q-page class="q-pa-md">
    <div class="row items-center no-wrap q-mb-sm">
      <div class="text-h6">회독</div>
      <q-space />
      <q-btn
        flat
        round
        dense
        color="grey-8"
        icon="delete_outline"
        aria-label="회독 진행 및 회독 횟수 초기화"
        @click="confirmClearReadingProgress"
      />
    </div>
    <div class="column q-gutter-sm">
      <q-btn
        v-for="sub in subjects"
        :key="sub"
        align="left"
        color="primary"
        outline
        no-caps
        padding="sm md"
        size="lg"
        class="full-width"
        :label="sub"
        @click="goSessions(sub)"
      />
    </div>

    <div class="text-h6 q-mt-lg q-mb-sm">모의고사</div>
    <div class="column q-gutter-sm">
      <template v-for="sub in subjects" :key="'mock-' + sub">
        <q-btn
          align="left"
          color="secondary"
          outline
          no-caps
          padding="sm md"
          size="lg"
          class="full-width"
          :label="sub"
          @click="goMockExam(sub)"
        />

        <q-card v-if="mockBannerFor(sub)" flat bordered class="q-mt-xs">
          <q-card-section class="text-body2">
            <div class="text-subtitle2 text-weight-medium q-mb-xs">
              진행 중인 모의고사 ({{ sub }})
            </div>
            <div class="q-mb-xs">
              현재 {{ displayCurrentIndex }} / 총 {{ mockSession!.questions.length }}문항
            </div>
            <div class="q-mb-xs">
              작성 완료 {{ answeredCount }} / {{ mockSession!.questions.length }}문항
            </div>
            <div class="text-caption text-grey-7">경과 {{ elapsedLabel }}</div>
          </q-card-section>
          <q-card-actions class="q-px-md q-pb-md q-gutter-sm">
            <q-btn
              unelevated
              no-caps
              color="primary"
              class="col"
              label="이어서 풀기"
              @click="goMockExam(sub)"
            />
            <q-btn
              outline
              no-caps
              color="negative"
              class="col"
              label="모의고사 종료하기"
              @click="confirmEndMockExam"
            />
          </q-card-actions>
        </q-card>
      </template>
    </div>

    <div class="row items-center no-wrap q-mt-lg q-mb-xs">
      <div class="text-h6">모의고사 이력</div>
      <q-space />
      <q-btn
        flat
        round
        dense
        color="grey-8"
        icon="delete_outline"
        :disable="mockHistory.length === 0"
        aria-label="모의고사 이력 삭제"
        @click.stop="confirmClearMockHistory"
      />
    </div>
    <q-separator class="q-mb-sm" />

    <div class="column q-gutter-sm">
      <q-card
        v-for="(entry, idx) in mockHistory"
        :key="historyRowKey(entry, idx)"
        flat
        bordered
        class="mock-history-card cursor-pointer"
        @click="goMockReview(entry)"
      >
        <q-card-section class="text-body2">
          <div class="row items-start no-wrap q-mb-sm">
            <div class="text-subtitle1 text-weight-bold">{{ entry.subject }}</div>
            <q-space />
            <div
              class="text-weight-medium"
              :class="entry.isPassed ? 'text-grey-9' : 'text-negative'"
            >
              {{ entry.isPassed ? '합격' : '불합격' }}
            </div>
          </div>
          <div class="column q-gutter-xs text-body2 text-grey-9">
            <div>시작: {{ formatHistoryStart(entry) }}</div>
            <div>경과: {{ formatHistoryElapsed(entry) }}</div>
            <div>문항 {{ historyTotalQuestions(entry) }} · 정답 {{ entry.correctCount }}</div>
          </div>
          <div class="row justify-end q-mt-sm">
            <span class="text-subtitle1 text-weight-bold">{{ historyScorePercent(entry) }}점</span>
          </div>
        </q-card-section>
      </q-card>
      <div v-if="mockHistory.length === 0" class="text-body2 text-grey-7 mock-history-empty">
        저장된 모의고사 이력이 없습니다.
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import {
  clearCurrentMockExam,
  clearMockHistory,
  readCurrentMockExam,
  readMockHistory,
} from 'src/exam/mockExamStorage';
import { clearAllExamProgressAndRepeat } from 'src/exam/examProgress';
import type { MockExamHistoryEntry, MockExamState } from 'src/types/mockExam';

const subjects = ['민법', '회계원리', '공동주택시설개론'] as const;

const router = useRouter();
const $q = useQuasar();

const mockSession = ref<MockExamState | null>(null);
const mockHistory = ref<MockExamHistoryEntry[]>([]);
const now = ref(Date.now());
let tickTimer: number | null = null;

function mockBannerFor(sub: string): boolean {
  const s = mockSession.value;
  return !!(s && s.subject === sub && s.questions?.length);
}

const mockInProgress = computed(() => {
  const s = mockSession.value;
  return !!s?.questions?.length;
});

const displayCurrentIndex = computed(() => {
  const s = mockSession.value;
  if (!s?.questions.length) return 0;
  return Math.min(s.currentIndex + 1, s.questions.length);
});

const answeredCount = computed(() => {
  const s = mockSession.value;
  if (!s?.answers) return 0;
  return s.answers.filter((a) => a != null).length;
});

const elapsedLabel = computed(() => {
  const s = mockSession.value;
  if (!s?.startedAt) return '—';
  const ms = Math.max(0, now.value - s.startedAt);
  const m = Math.floor(ms / 60_000);
  const sec = Math.floor((ms % 60_000) / 1000);
  return `${m}:${String(sec).padStart(2, '0')}`;
});

function refreshMockHistory(): void {
  mockHistory.value = [...readMockHistory()].sort((a, b) => b.endedAt - a.endedAt);
}

function historyRowKey(entry: MockExamHistoryEntry, idx: number): string {
  return `${entry.endedAt}-${idx}-${entry.subject}`;
}

function historyTotalQuestions(entry: MockExamHistoryEntry): number {
  return entry.questions?.length ?? 0;
}

function formatHistoryStart(entry: MockExamHistoryEntry): string {
  const ts = entry.startedAt ?? entry.endedAt;
  return new Date(ts).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function formatHistoryElapsed(entry: MockExamHistoryEntry): string {
  const start = entry.startedAt ?? entry.endedAt;
  const ms = Math.max(0, entry.endedAt - start);
  const m = Math.floor(ms / 60_000);
  const s = Math.floor((ms % 60_000) / 1000);
  return `${m}분 ${s}초`;
}

function historyScorePercent(entry: MockExamHistoryEntry): number {
  const n = historyTotalQuestions(entry);
  if (n <= 0) return 0;
  return Math.round((entry.correctCount / n) * 100);
}

function confirmClearReadingProgress() {
  $q.dialog({
    title: '회독 초기화',
    message:
      '모든 과목·회차의 회독 진행 위치와 회독 횟수를 초기화할까요? 이 작업은 되돌릴 수 없습니다.',
    persistent: true,
    ok: {
      label: '초기화',
      color: 'negative',
      noCaps: true,
    },
    cancel: {
      label: '취소',
      flat: true,
      noCaps: true,
    },
  }).onOk(() => {
    clearAllExamProgressAndRepeat();
    $q.notify({ type: 'info', message: '회독 진행 및 회독 횟수를 초기화했습니다.' });
  });
}

function confirmClearMockHistory() {
  if (!mockHistory.value.length) return;
  $q.dialog({
    title: '이력 삭제',
    message: '모든 모의고사 이력을 삭제할까요?',
    persistent: true,
    ok: {
      label: '삭제',
      color: 'negative',
      noCaps: true,
    },
    cancel: {
      label: '취소',
      flat: true,
      noCaps: true,
    },
  }).onOk(() => {
    clearMockHistory();
    refreshMockHistory();
    $q.notify({ type: 'info', message: '모의고사 이력을 삭제했습니다.' });
  });
}

function refreshMockBanner(): void {
  const raw = readCurrentMockExam();
  const known = subjects as readonly string[];
  if (raw && raw.questions?.length && known.includes(raw.subject)) {
    mockSession.value = raw;
  } else {
    mockSession.value = null;
  }
  now.value = Date.now();
}

function syncTickTimer(): void {
  if (tickTimer != null) {
    window.clearInterval(tickTimer);
    tickTimer = null;
  }
  if (mockInProgress.value) {
    tickTimer = window.setInterval(() => {
      now.value = Date.now();
    }, 1000);
  }
}

watch(mockInProgress, syncTickTimer, { immediate: true });

function goSessions(subject: string) {
  void router.push({ name: 'exam-sessions', params: { subject } });
}

function goMockExam(subject: string) {
  void router.push({ name: 'exam-mock', params: { subject } });
}

function goMockReview(entry: MockExamHistoryEntry) {
  void router.push({
    name: 'exam-mock-review',
    params: { subject: entry.subject, endedAt: String(entry.endedAt) },
  });
}

function confirmEndMockExam() {
  $q.dialog({
    title: '모의고사 종료',
    message: '진행 중인 모의고사를 삭제하고 종료할까요?',
    persistent: true,
    ok: {
      label: '종료',
      color: 'negative',
      noCaps: true,
    },
    cancel: {
      label: '취소',
      flat: true,
      noCaps: true,
    },
  }).onOk(() => {
    clearCurrentMockExam();
    refreshMockBanner();
    $q.notify({ type: 'info', message: '모의고사를 종료했습니다.' });
  });
}

onMounted(() => {
  refreshMockBanner();
  refreshMockHistory();
});

onActivated(() => {
  refreshMockBanner();
  refreshMockHistory();
});

onUnmounted(() => {
  if (tickTimer != null) {
    window.clearInterval(tickTimer);
    tickTimer = null;
  }
});
</script>

<style scoped>
/* 모의고사 이력 카드: 다크에서 회색 유틸 대비·카드 배경 */
.body--dark .mock-history-card {
  background-color: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.14);
}

.body--dark .mock-history-card:hover {
  background-color: rgba(255, 255, 255, 0.09);
}

.body--dark .mock-history-card .text-grey-9 {
  color: rgba(255, 255, 255, 0.78) !important;
}

.body--dark .mock-history-card .text-subtitle1 {
  color: rgba(255, 255, 255, 0.95) !important;
}

.body--dark .mock-history-empty {
  color: rgba(255, 255, 255, 0.55) !important;
}
</style>
