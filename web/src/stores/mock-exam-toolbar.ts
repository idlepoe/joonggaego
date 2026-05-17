import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref } from 'vue';

export const useMockExamToolbarStore = defineStore('mockExamToolbar', () => {
  const timerLabel = ref('\u00a0');
  /** AnswerSheet 헤더와 동일: 시험·과목 / 문항 진행 */
  const line1 = ref('');
  const line2 = ref('');
  const submitNonce = ref(0);
  const reviewNonce = ref(0);

  function setTimerLabel(s: string) {
    timerLabel.value = s || '\u00a0';
  }

  function setMockToolbarLines(a: string, b: string) {
    line1.value = a;
    line2.value = b;
  }

  function requestSubmit() {
    submitNonce.value++;
  }

  function requestAnswerReview() {
    reviewNonce.value++;
  }

  function clearToolbar() {
    timerLabel.value = '\u00a0';
    line1.value = '';
    line2.value = '';
    submitNonce.value = 0;
    reviewNonce.value = 0;
  }

  return {
    timerLabel,
    line1,
    line2,
    submitNonce,
    reviewNonce,
    setTimerLabel,
    setMockToolbarLines,
    requestSubmit,
    requestAnswerReview,
    clearToolbar,
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useMockExamToolbarStore, import.meta.hot));
}
