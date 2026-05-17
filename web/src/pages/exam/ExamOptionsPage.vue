<template>
  <q-page padding class="q-pb-xl">
    <q-list bordered separator class="rounded-borders">
      <q-item>
        <q-item-section>
          <q-item-label>테마</q-item-label>
          <q-item-label caption>시스템 설정을 따르거나 라이트/다크로 고정합니다.</q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-btn-toggle
            :model-value="themeMode"
            spread
            no-caps
            unelevated
            toggle-color="primary"
            color="grey-3"
            text-color="grey-8"
            :options="themeOptions"
            @update:model-value="onThemeChange"
          />
        </q-item-section>
      </q-item>

      <q-item clickable @click="openCorrectColorDialog">
        <q-item-section>
          <q-item-label>정답 하이라이트 배경</q-item-label>
          <q-item-label caption>답안지·모의복습에서 정답 보기 카드 배경에 사용합니다.</q-item-label>
        </q-item-section>
        <q-item-section side>
          <div class="row items-center q-gutter-sm no-wrap">
            <div
              class="exam-options-swatch exam-options-swatch--fixed-palette rounded-borders"
              :style="{ backgroundColor: correctHighlightHex }"
            />
            <q-icon name="chevron_right" color="grey-6" />
          </div>
        </q-item-section>
      </q-item>

      <q-item clickable @click="openCorrectTextColorDialog">
        <q-item-section>
          <q-item-label>정답 하이라이트 글자 색</q-item-label>
          <q-item-label caption>정답으로 표시된 보기 안의 글자 색입니다.</q-item-label>
        </q-item-section>
        <q-item-section side>
          <div class="row items-center q-gutter-sm no-wrap">
            <div
              class="exam-options-swatch exam-options-swatch--fixed-palette rounded-borders"
              :style="{ backgroundColor: correctHighlightTextHex }"
            />
            <q-icon name="chevron_right" color="grey-6" />
          </div>
        </q-item-section>
      </q-item>

      <q-item clickable @click="openPickChoiceColorDialog">
        <q-item-section>
          <q-item-label>모의고사 선택 보기 배경</q-item-label>
          <q-item-label caption>모의고사 풀이에서 선택한 보기 카드 배경에 사용합니다.</q-item-label>
        </q-item-section>
        <q-item-section side>
          <div class="row items-center q-gutter-sm no-wrap">
            <div
              class="exam-options-swatch exam-options-swatch--fixed-palette rounded-borders"
              :style="{ backgroundColor: pickChoiceHighlightHex }"
            />
            <q-icon name="chevron_right" color="grey-6" />
          </div>
        </q-item-section>
      </q-item>

      <q-item clickable @click="openPickChoiceTextColorDialog">
        <q-item-section>
          <q-item-label>모의고사 선택 보기 글자 색</q-item-label>
          <q-item-label caption>선택한 보기 카드 안의 글자 색입니다.</q-item-label>
        </q-item-section>
        <q-item-section side>
          <div class="row items-center q-gutter-sm no-wrap">
            <div
              class="exam-options-swatch exam-options-swatch--fixed-palette rounded-borders"
              :style="{ backgroundColor: pickChoiceHighlightTextHex }"
            />
            <q-icon name="chevron_right" color="grey-6" />
          </div>
        </q-item-section>
      </q-item>

      <q-item>
        <q-item-section>
          <q-item-label>하단 버튼 영역 높이</q-item-label>
          <q-item-label caption>이전·다음 툴바의 최소 높이입니다.</q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-btn-toggle
            :model-value="stickyButtonHeight"
            spread
            no-caps
            unelevated
            toggle-color="primary"
            color="grey-3"
            text-color="grey-8"
            :options="heightOptions"
            @update:model-value="onHeightChange"
          />
        </q-item-section>
      </q-item>

      <q-item>
        <q-item-section>
          <q-item-label>문제 글자 크기</q-item-label>
          <q-item-label caption>문제 본문(번호·지문)에 적용됩니다.</q-item-label>
        </q-item-section>
        <q-item-section side style="min-width: 0">
          <q-btn-toggle
            :model-value="questionTextSize"
            spread
            no-caps
            dense
            unelevated
            toggle-color="primary"
            color="grey-3"
            text-color="grey-8"
            :options="textSizeOptions"
            @update:model-value="onTextSizeChange"
          />
        </q-item-section>
      </q-item>

      <q-item>
        <q-item-section>
          <q-item-label>하단 버튼 순서</q-item-label>
          <q-item-label caption>이전/다음 버튼의 좌우 배치입니다.</q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-option-group
            :model-value="stickyButtonOrder"
            type="radio"
            :options="orderOptions"
            color="primary"
            @update:model-value="onOrderChange"
          />
        </q-item-section>
      </q-item>
    </q-list>

    <div class="q-mt-lg">
      <div class="text-subtitle2 text-weight-medium q-mb-xs">답안지 화면 미리보기</div>
      <div class="text-caption text-grey-7 q-mb-sm">
        실제 답안지·모의고사 풀이와 같은 문제 본문 클래스·하단 이전/다음 버튼(순서·높이)이
        반영됩니다.
      </div>
      <q-card flat bordered class="rounded-borders overflow-hidden exam-options-sheet-preview">
        <q-card-section class="q-pa-md">
          <div class="q-mb-md" :class="questionTextClass" style="white-space: pre-wrap">
            1. (예시) 시험 문제 본문은 위에서 선택한 글자 크기로 표시됩니다.
          </div>
          <div class="column q-gutter-sm">
            <q-card flat bordered class="q-pa-md">
              <div :class="choiceTextClass">
                <span class="text-weight-bold">1.</span>
                첫 번째 보기 문장입니다.
              </div>
            </q-card>
            <q-card flat bordered class="q-pa-md exam-correct-highlight">
              <div :class="choiceTextClass">
                <span class="text-weight-bold">2.</span>
                정답 보기(배경·글자 색)
              </div>
            </q-card>
            <q-card flat bordered class="q-pa-md exam-mock-choice-selected">
              <div :class="choiceTextClass">
                <span class="text-weight-bold">3.</span>
                모의고사에서 고른 보기(배경·글자 색)
              </div>
            </q-card>
          </div>
        </q-card-section>
        <div class="exam-options-sheet-preview-toolbar">
          <ExamSheetNavToolbar
            :prev-disabled="false"
            :next-disabled="false"
            @prev="onSheetPreviewNav"
            @next="onSheetPreviewNav"
          />
        </div>
      </q-card>
    </div>

    <q-dialog v-model="colorDialogOpen">
      <q-card class="bg-white text-grey-9 exam-options-color-dialog" style="min-width: 280px">
        <q-card-section class="text-h6">{{ colorDialogTitle }}</q-card-section>
        <q-card-section class="q-pt-none">
          <q-color v-model="colorDraft" default-view="palette" format-model="hex" :dark="false" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="취소" color="grey-8" no-caps @click="colorDialogOpen = false" />
          <q-btn unelevated label="확인" color="primary" no-caps @click="confirmColor" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import type {
  ExamThemeMode,
  QuestionTextSize,
  StickyButtonHeight,
  StickyButtonOrder,
} from 'src/exam/examUserOptions';
import { useExamUserOptionsStore } from 'stores/exam-user-options';
import ExamSheetNavToolbar from 'src/components/exam/ExamSheetNavToolbar.vue';

const store = useExamUserOptionsStore();
const {
  themeMode,
  correctHighlightHex,
  correctHighlightTextHex,
  pickChoiceHighlightHex,
  pickChoiceHighlightTextHex,
  stickyButtonHeight,
  questionTextSize,
  stickyButtonOrder,
} = storeToRefs(store);

const questionTextClass = computed(
  () => `text-body1 exam-question-text--${questionTextSize.value}`,
);

const choiceTextClass = computed(() => `text-body2 exam-question-text--${questionTextSize.value}`);

const colorDialogKind = ref<'correct' | 'correctText' | 'pick' | 'pickText'>('correct');
const colorDialogTitle = computed(() => {
  switch (colorDialogKind.value) {
    case 'correct':
      return '정답 하이라이트 배경';
    case 'correctText':
      return '정답 하이라이트 글자 색';
    case 'pick':
      return '모의고사 선택 보기 배경';
    case 'pickText':
      return '모의고사 선택 보기 글자 색';
    default:
      return '';
  }
});

const colorDialogFallbackHex = computed(() => {
  switch (colorDialogKind.value) {
    case 'correct':
      return correctHighlightHex.value;
    case 'correctText':
      return correctHighlightTextHex.value;
    case 'pick':
      return pickChoiceHighlightHex.value;
    case 'pickText':
      return pickChoiceHighlightTextHex.value;
    default:
      return correctHighlightHex.value;
  }
});

const themeOptions = [
  { label: '시스템', value: 'system' as ExamThemeMode },
  { label: '라이트', value: 'light' as ExamThemeMode },
  { label: '다크', value: 'dark' as ExamThemeMode },
];

const heightOptions = [
  { label: '보통', value: 'normal' as StickyButtonHeight },
  { label: '크게', value: 'large' as StickyButtonHeight },
  { label: '더 크게', value: 'xlarge' as StickyButtonHeight },
];

const textSizeOptions = [
  { label: '아주 작게', value: 'sm' as QuestionTextSize },
  { label: '작게', value: 'md' as QuestionTextSize },
  { label: '보통', value: 'lg' as QuestionTextSize },
  { label: '크게', value: 'xl' as QuestionTextSize },
  { label: '최대', value: 'max' as QuestionTextSize },
];

const orderOptions = [
  { label: '이전 | 다음', value: 'prev-next' as StickyButtonOrder },
  { label: '다음 | 이전', value: 'next-prev' as StickyButtonOrder },
];

const colorDialogOpen = ref(false);
const colorDraft = ref(correctHighlightHex.value);

watch(colorDialogOpen, (open) => {
  if (open) {
    colorDraft.value = colorDialogFallbackHex.value;
  }
});

function onThemeChange(v: ExamThemeMode) {
  store.patchAndPersist({ themeMode: v });
}

function onHeightChange(v: StickyButtonHeight) {
  store.patchAndPersist({ stickyButtonHeight: v });
}

function onTextSizeChange(v: QuestionTextSize) {
  store.patchAndPersist({ questionTextSize: v });
}

function onOrderChange(v: StickyButtonOrder) {
  store.patchAndPersist({ stickyButtonOrder: v });
}

function onSheetPreviewNav() {
  /* 답안지 레이아웃 미리보기: 문항 이동 없음 */
}

function openCorrectColorDialog() {
  colorDialogKind.value = 'correct';
  colorDraft.value = correctHighlightHex.value;
  colorDialogOpen.value = true;
}

function openCorrectTextColorDialog() {
  colorDialogKind.value = 'correctText';
  colorDraft.value = correctHighlightTextHex.value;
  colorDialogOpen.value = true;
}

function openPickChoiceTextColorDialog() {
  colorDialogKind.value = 'pickText';
  colorDraft.value = pickChoiceHighlightTextHex.value;
  colorDialogOpen.value = true;
}

function openPickChoiceColorDialog() {
  colorDialogKind.value = 'pick';
  colorDraft.value = pickChoiceHighlightHex.value;
  colorDialogOpen.value = true;
}

function normalizeHexFromColor(v: string | Record<string, unknown>): string {
  if (typeof v === 'string') return v;
  if (v && typeof v === 'object' && 'r' in v && 'g' in v && 'b' in v) {
    const r = Number((v as { r: number }).r);
    const g = Number((v as { g: number }).g);
    const b = Number((v as { b: number }).b);
    const toHex = (n: number) =>
      Math.min(255, Math.max(0, Math.round(n)))
        .toString(16)
        .padStart(2, '0');
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
  }
  return colorDialogFallbackHex.value;
}

function confirmColor() {
  const hex = normalizeHexFromColor(colorDraft.value as string | Record<string, unknown>);
  if (colorDialogKind.value === 'correct') {
    store.patchAndPersist({ correctHighlightHex: hex });
  } else if (colorDialogKind.value === 'correctText') {
    store.patchAndPersist({ correctHighlightTextHex: hex });
  } else if (colorDialogKind.value === 'pick') {
    store.patchAndPersist({ pickChoiceHighlightHex: hex });
  } else {
    store.patchAndPersist({ pickChoiceHighlightTextHex: hex });
  }
  colorDialogOpen.value = false;
}
</script>

<style scoped>
/* 다크 테마여도 사용자가 고른 RGB는 그대로 보이도록(브라우저 색 보정·테두리만 분기하지 않음) */
.exam-options-swatch--fixed-palette {
  color-scheme: light;
  forced-color-adjust: none;
}
.exam-options-swatch {
  width: 28px;
  height: 28px;
  border: 1px solid rgba(0, 0, 0, 0.18);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
}
.exam-options-color-dialog {
  color-scheme: light;
}
/* 미리보기 카드: 답안지 본문 영역과 비슷한 배경 대비 */
.exam-options-sheet-preview {
  max-width: 100%;
}
.exam-options-sheet-preview-toolbar {
  width: 100%;
}
</style>
