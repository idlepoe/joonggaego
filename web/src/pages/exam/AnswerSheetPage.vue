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
          class="q-pa-md"
          :class="{ 'exam-correct-highlight': c.no === current.correct_answer }"
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
      이 회차·과목에 해당하는 문항이 없습니다.
    </div>
    <div v-if="loadError" class="text-negative">{{ loadError }}</div>

    <q-page-sticky
      v-if="!loading && questions.length > 0"
      class="exam-sheet-nav-sticky-wrap"
      position="bottom"
      expand
    >
      <ExamSheetNavToolbar
        :prev-disabled="index <= 0"
        :next-disabled="false"
        @prev="prev"
        @next="next"
      />
    </q-page-sticky>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import type { ExamQuestion } from 'src/types/exam';
import {
  fetchExamSessionsManifest,
  listSessionsFromManifest,
  loadSessionFromRemote,
} from 'src/exam/examRemote';
import {
  readExamProgress,
  writeExamProgress,
  incrementRepeatCount,
  resetExamProgress,
} from 'src/exam/examProgress';
import { useExamSheetToolbarStore } from 'stores/exam-sheet-toolbar';
import { useExamUserOptionsStore } from 'stores/exam-user-options';
import ExamOptionalRemoteImage from 'src/components/exam/ExamOptionalRemoteImage.vue';
import ExamSheetNavToolbar from 'src/components/exam/ExamSheetNavToolbar.vue';
import { examChoiceImageUrl, examQuestionImageUrl } from 'src/exam/constants';

const props = defineProps<{
  subject: string;
  session: string;
}>();

const router = useRouter();
const $q = useQuasar();
const toolbarStore = useExamSheetToolbarStore();
const examUserOpts = useExamUserOptionsStore();
const { questionTextSize } = storeToRefs(examUserOpts);

const questionTextClass = computed(
  () => `text-body1 exam-question-text--${questionTextSize.value}`,
);

const choiceTextClass = computed(() => `text-body2 exam-question-text--${questionTextSize.value}`);

const loading = ref(true);
const loadError = ref('');
const questions = ref<ExamQuestion[]>([]);
const index = ref(0);

const current = computed(() => questions.value[index.value] ?? null);
const total = computed(() => questions.value.length);
const displayIndex = computed(() => (total.value ? index.value + 1 : 0));

onMounted(async () => {
  loading.value = true;
  loadError.value = '';
  try {
    const all = await loadSessionFromRemote(props.session);
    const filtered = all
      .filter((q) => q.subject === props.subject)
      .sort((a, b) => a.question_number - b.question_number);
    questions.value = filtered;
    if (filtered.length > 0) {
      index.value = readExamProgress(props.subject, props.session, filtered.length);
    }
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    loadError.value = `문제를 불러오지 못했습니다: ${msg}`;
    $q.notify({ type: 'negative', message: loadError.value });
  } finally {
    loading.value = false;
  }
});

const toolbarStatusLines = computed(() => {
  if (loading.value) {
    return {
      line1: `${props.subject} · ${props.session}`,
      line2: '',
    };
  }
  const c = current.value;
  if (!c || total.value === 0) {
    return {
      line1: `${props.subject} · ${props.session}`,
      line2: '',
    };
  }
  return {
    line1: `${c.exam_type} ${c.subject} · ${props.session}`,
    line2: `${displayIndex.value}(현재문항)/${total.value}(총문항)`,
  };
});

watch(
  toolbarStatusLines,
  ({ line1, line2 }) => {
    toolbarStore.setSheetToolbarLines(line1, line2);
  },
  { immediate: true },
);

onUnmounted(() => {
  toolbarStore.clearSheetToolbar();
});

watch(index, (i) => {
  if (questions.value.length > 0) {
    writeExamProgress(props.subject, props.session, i);
  }
});

const finishSessionCleanup = () => {
  incrementRepeatCount(props.subject, props.session);
  resetExamProgress(props.subject, props.session);
};

/** manifest 내림차순에서 한 칸 아래(이전 연도) 회차 */
const goToNextSessionOrList = async (): Promise<void> => {
  try {
    const manifest = await fetchExamSessionsManifest();
    const sessions = listSessionsFromManifest(manifest);
    const idx = sessions.indexOf(props.session);
    const nextSession = idx >= 0 && idx < sessions.length - 1 ? sessions[idx + 1] : null;
    if (!nextSession) {
      $q.notify({ type: 'info', message: '마지막 회차입니다.' });
      void router.push({ name: 'exam-sessions', params: { subject: props.subject } });
      return;
    }
    void router.push({
      name: 'exam-sheet',
      params: { subject: props.subject, session: nextSession },
    });
  } catch {
    void router.push({ name: 'exam-sessions', params: { subject: props.subject } });
  }
};

function prev() {
  if (index.value > 0) index.value--;
}

function next() {
  if (index.value < questions.value.length - 1) {
    index.value++;
    return;
  }
  $q.dialog({
    title: '안내',
    message: '문제를 모두 확인했습니다.',
    persistent: true,
    ok: {
      label: '목록으로 돌아가기',
      color: 'primary',
      noCaps: true,
    },
    cancel: {
      label: '다음 회차로',
      flat: true,
      color: 'secondary',
      noCaps: true,
    },
  })
    .onOk(() => {
      finishSessionCleanup();
      void router.push({ name: 'exam-sessions', params: { subject: props.subject } });
    })
    .onCancel(async () => {
      finishSessionCleanup();
      await goToNextSessionOrList();
    });
}
</script>
