import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref } from 'vue';
import type { ExamUserOptions } from 'src/exam/examUserOptions';
import {
  mergeExamUserOptionsPatch,
  readExamUserOptions,
  writeExamUserOptions,
  syncExamUserOptionsToDom,
} from 'src/exam/examUserOptions';

function assignFromOptions(
  target: {
    themeMode: ReturnType<typeof ref<ExamUserOptions['themeMode']>>;
    correctHighlightHex: ReturnType<typeof ref<string>>;
    correctHighlightTextHex: ReturnType<typeof ref<string>>;
    pickChoiceHighlightHex: ReturnType<typeof ref<string>>;
    pickChoiceHighlightTextHex: ReturnType<typeof ref<string>>;
    stickyButtonHeight: ReturnType<typeof ref<ExamUserOptions['stickyButtonHeight']>>;
    questionTextSize: ReturnType<typeof ref<ExamUserOptions['questionTextSize']>>;
    stickyButtonOrder: ReturnType<typeof ref<ExamUserOptions['stickyButtonOrder']>>;
  },
  o: ExamUserOptions,
) {
  target.themeMode.value = o.themeMode;
  target.correctHighlightHex.value = o.correctHighlightHex;
  target.correctHighlightTextHex.value = o.correctHighlightTextHex;
  target.pickChoiceHighlightHex.value = o.pickChoiceHighlightHex;
  target.pickChoiceHighlightTextHex.value = o.pickChoiceHighlightTextHex;
  target.stickyButtonHeight.value = o.stickyButtonHeight;
  target.questionTextSize.value = o.questionTextSize;
  target.stickyButtonOrder.value = o.stickyButtonOrder;
}

export const useExamUserOptionsStore = defineStore('examUserOptions', () => {
  const initial = readExamUserOptions();

  const themeMode = ref(initial.themeMode);
  const correctHighlightHex = ref(initial.correctHighlightHex);
  const correctHighlightTextHex = ref(initial.correctHighlightTextHex);
  const pickChoiceHighlightHex = ref(initial.pickChoiceHighlightHex);
  const pickChoiceHighlightTextHex = ref(initial.pickChoiceHighlightTextHex);
  const stickyButtonHeight = ref(initial.stickyButtonHeight);
  const questionTextSize = ref(initial.questionTextSize);
  const stickyButtonOrder = ref(initial.stickyButtonOrder);

  const refs = {
    themeMode,
    correctHighlightHex,
    correctHighlightTextHex,
    pickChoiceHighlightHex,
    pickChoiceHighlightTextHex,
    stickyButtonHeight,
    questionTextSize,
    stickyButtonOrder,
  };

  function snapshot(): ExamUserOptions {
    return {
      themeMode: themeMode.value,
      correctHighlightHex: correctHighlightHex.value,
      correctHighlightTextHex: correctHighlightTextHex.value,
      pickChoiceHighlightHex: pickChoiceHighlightHex.value,
      pickChoiceHighlightTextHex: pickChoiceHighlightTextHex.value,
      stickyButtonHeight: stickyButtonHeight.value,
      questionTextSize: questionTextSize.value,
      stickyButtonOrder: stickyButtonOrder.value,
    };
  }

  function hydrateFromStorage() {
    const next = readExamUserOptions();
    assignFromOptions(refs, next);
    syncExamUserOptionsToDom(next);
  }

  function patchAndPersist(patch: Partial<ExamUserOptions>) {
    const next = mergeExamUserOptionsPatch(snapshot(), patch);
    assignFromOptions(refs, next);
    writeExamUserOptions(next);
    syncExamUserOptionsToDom(next);
  }

  return {
    themeMode,
    correctHighlightHex,
    correctHighlightTextHex,
    pickChoiceHighlightHex,
    pickChoiceHighlightTextHex,
    stickyButtonHeight,
    questionTextSize,
    stickyButtonOrder,
    hydrateFromStorage,
    patchAndPersist,
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useExamUserOptionsStore, import.meta.hot));
}
