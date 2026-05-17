import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref } from 'vue';

/** AnswerSheet → ExamLayout 헤더 2줄(시험·과목 / 문항 진행) */
export const useExamSheetToolbarStore = defineStore('examSheetToolbar', () => {
  const line1 = ref('');
  const line2 = ref('');

  function setSheetToolbarLines(a: string, b: string) {
    line1.value = a;
    line2.value = b;
  }

  function clearSheetToolbar() {
    line1.value = '';
    line2.value = '';
  }

  return { line1, line2, setSheetToolbarLines, clearSheetToolbar };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useExamSheetToolbarStore, import.meta.hot));
}
