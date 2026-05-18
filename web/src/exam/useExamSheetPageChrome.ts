import {
  computed,
  nextTick,
  onUnmounted,
  ref,
  watch,
  type ComponentPublicInstance,
  type ComputedRef,
  type Ref,
  type WatchSource,
} from 'vue';

type StickyRefTarget = ComponentPublicInstance | HTMLElement | null;

function resolveStickyElement(target: StickyRefTarget): HTMLElement | null {
  if (!target) return null;
  if (target instanceof HTMLElement) return target;
  const el = target.$el;
  return el instanceof HTMLElement ? el : null;
}

/** ExamLayout / MainLayout 스크롤 컨테이너 */
export function getExamPageScrollEl(): HTMLElement {
  const container = document.getElementById('app-shell')?.querySelector('.q-page-container');
  if (container instanceof HTMLElement) return container;
  return document.documentElement;
}

export function scrollExamPageToTop(): void {
  void nextTick(() => {
    const el = getExamPageScrollEl();
    el.scrollTop = 0;
    if (el !== document.documentElement) {
      window.scrollTo(0, 0);
    }
  });
}

/** 하단 q-page-sticky 네비 높이에 맞춰 페이지 하단 패딩을 맞춤 */
export function useExamSheetBottomInset(
  stickyRef: Ref<StickyRefTarget>,
  visible: Ref<boolean> | ComputedRef<boolean>,
) {
  const bottomInsetPx = ref(0);
  let observer: ResizeObserver | null = null;

  const disconnect = () => {
    observer?.disconnect();
    observer = null;
  };

  const measure = () => {
    if (!visible.value) {
      bottomInsetPx.value = 0;
      return;
    }
    const el = resolveStickyElement(stickyRef.value);
    bottomInsetPx.value = el ? Math.ceil(el.getBoundingClientRect().height) : 0;
  };

  const bind = () => {
    disconnect();
    if (!visible.value) {
      bottomInsetPx.value = 0;
      return;
    }
    const el = resolveStickyElement(stickyRef.value);
    if (!el) {
      bottomInsetPx.value = 0;
      return;
    }
    observer = new ResizeObserver(() => measure());
    observer.observe(el);
    measure();
  };

  watch(
    [stickyRef, visible],
    () => {
      void nextTick(bind);
    },
    { immediate: true },
  );

  onUnmounted(disconnect);

  const pageStyle = computed(() =>
    bottomInsetPx.value > 0 ? { paddingBottom: `${bottomInsetPx.value}px` } : undefined,
  );

  return { pageStyle };
}

/** 문항·회차 등 전환 시 본문 스크롤을 맨 위로 */
export function useExamQuestionScrollToTop(sources: WatchSource<unknown>[]) {
  watch(sources, () => scrollExamPageToTop(), { flush: 'post' });
}
