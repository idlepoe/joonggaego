<template>
  <section v-if="visible" class="exam-ai-explanation q-mt-md q-mb-lg">
    <q-card flat bordered class="q-pa-md">
      <div class="text-subtitle2 text-weight-bold q-mb-md">해설</div>

      <div v-if="explanation!.correctExplanation?.trim()" class="q-mb-md">
        <div class="text-caption text-weight-bold text-grey-7 q-mb-xs">정답 해설</div>
        <div :class="bodyClass" class="exam-ai-explanation-body" style="white-space: pre-wrap">
          {{ explanation!.correctExplanation }}
        </div>
      </div>

      <div v-if="explanation!.wrongAnswerNotes?.length" class="q-mb-md">
        <div class="text-caption text-weight-bold text-grey-7 q-mb-xs">보기별 해설</div>
        <ul class="exam-ai-explanation-notes q-pl-md q-my-none" :class="bodyClass">
          <li
            v-for="(note, i) in explanation!.wrongAnswerNotes"
            :key="i"
            class="q-mb-xs"
            style="white-space: pre-wrap"
          >
            {{ note }}
          </li>
        </ul>
      </div>

      <div v-if="explanation!.examTip?.trim()">
        <div class="text-caption text-weight-bold text-grey-7 q-mb-xs">시험 Tip</div>
        <div
          :class="bodyClass"
          class="exam-ai-explanation-tip exam-ai-explanation-body"
          style="white-space: pre-wrap"
        >
          {{ explanation!.examTip }}
        </div>
      </div>
    </q-card>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  hasDisplayableAiExplanation,
  type ExamAiExplanation,
} from 'src/types/exam';

const props = defineProps<{
  explanation: ExamAiExplanation | null | undefined;
  bodyClass?: string;
}>();

const visible = computed(() => hasDisplayableAiExplanation(props.explanation));
</script>

<style scoped>
.exam-ai-explanation-body {
  line-height: 1.5;
}

.exam-ai-explanation-notes {
  list-style: disc;
}

.exam-ai-explanation-tip {
  padding: 10px 12px;
  border-radius: 6px;
  background: rgba(21, 101, 192, 0.08);
}

.body--dark .exam-ai-explanation-tip {
  background: rgba(144, 202, 249, 0.12);
}
</style>
