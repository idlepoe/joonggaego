<template>
  <q-page class="q-pa-md full-width column session-list-page">
    <q-inner-loading :showing="loading" color="primary" />

    <div v-if="error" class="text-negative q-mb-md full-width">{{ error }}</div>

    <div v-else class="column q-gutter-sm full-width">
      <q-btn
        v-for="s in sessions"
        :key="s"
        align="left"
        color="secondary"
        outline
        no-caps
        class="full-width session-row-btn"
        padding="sm md"
        @click="openSheet(s)"
      >
        <div class="row items-center no-wrap full-width">
          <span class="col text-left ellipsis">{{ s }}</span>
          <div class="row items-center no-wrap shrink-0 q-gutter-x-sm">
            <span class="text-body2 text-weight-medium text-grey-9">
              {{ progressPercentLabel(s) }}
            </span>
            <span class="text-body2 text-weight-medium text-grey-9">
              {{ repeatCountLabel(s) }}
            </span>
          </div>
        </div>
      </q-btn>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import {
  fetchExamSessionsManifest,
  listSessionsFromManifest,
  loadSessionFromRemote,
} from 'src/exam/examRemote';
import { readExamProgress, readRepeatCount } from 'src/exam/examProgress';

const props = defineProps<{
  subject: string;
}>();

const router = useRouter();
const $q = useQuasar();

const loading = ref(true);
const error = ref('');
const sessions = ref<string[]>([]);
/** 회차별 해당 과목 문항 수 (로드 전이면 키 없음) */
const totalsBySession = ref<Record<string, number>>({});

/** 첫 문항(index 0)일 때 0%. 완료한 문항 수 기준: index / total */
function progressPercentLabel(session: string): string {
  const total = totalsBySession.value[session];
  if (total === undefined) return '—';
  if (total <= 0) return '0%';
  const idx = readExamProgress(props.subject, session, total);
  const pct = Math.min(100, Math.round((idx / total) * 100));
  return `${pct}%`;
}

function repeatCountLabel(session: string): string {
  return `회독 ${readRepeatCount(props.subject, session)}`;
}

async function loadQuestionTotals(sessionList: string[]): Promise<void> {
  const entries = await Promise.all(
    sessionList.map(async (s) => {
      try {
        const all = await loadSessionFromRemote(s);
        const n = all.filter((q) => q.subject === props.subject).length;
        return [s, n] as const;
      } catch {
        return [s, 0] as const;
      }
    }),
  );
  totalsBySession.value = Object.fromEntries(entries);
}

onMounted(async () => {
  loading.value = true;
  error.value = '';
  try {
    const manifest = await fetchExamSessionsManifest();
    const list = listSessionsFromManifest(manifest);
    sessions.value = list;
    await loadQuestionTotals(list);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    error.value = `회차 목록을 불러오지 못했습니다: ${msg}`;
    $q.notify({ type: 'negative', message: error.value });
  } finally {
    loading.value = false;
  }
});

function openSheet(session: string) {
  void router.push({
    name: 'exam-sheet',
    params: { subject: props.subject, session },
  });
}
</script>

<style scoped>
.session-list-page {
  min-width: 0;
  box-sizing: border-box;
}
.session-row-btn :deep(.q-btn__content) {
  width: 100%;
}
.shrink-0 {
  flex-shrink: 0;
}
</style>
