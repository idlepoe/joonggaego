import type { Pinia } from 'pinia';
import { useExamUserOptionsStore } from 'stores/exam-user-options';

export default function ({ store }: { store: Pinia }) {
  useExamUserOptionsStore(store).hydrateFromStorage();
}
