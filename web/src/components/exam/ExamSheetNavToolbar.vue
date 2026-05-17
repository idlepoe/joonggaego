<template>
  <q-toolbar
    class="text-grey-9 exam-page-sticky-toolbar exam-sheet-nav-toolbar-inner"
    :class="stickyToolbarHeightClass"
  >
    <template v-if="stickyButtonOrder === 'prev-next'">
      <q-btn
        :outline="isDarkNav"
        :unelevated="!isDarkNav"
        no-caps
        class="col"
        :size="navBtnSize"
        :color="prevBtnColor"
        :text-color="prevBtnTextColor"
        label="이전"
        :disable="prevDisabled"
        @click="emit('prev')"
      />
      <q-btn
        :outline="isDarkNav"
        :unelevated="!isDarkNav"
        no-caps
        class="col"
        :size="navBtnSize"
        color="primary"
        :text-color="isDarkNav ? undefined : 'white'"
        label="다음"
        :disable="nextDisabled"
        @click="emit('next')"
      />
    </template>
    <template v-else>
      <q-btn
        :outline="isDarkNav"
        :unelevated="!isDarkNav"
        no-caps
        class="col"
        :size="navBtnSize"
        color="primary"
        :text-color="isDarkNav ? undefined : 'white'"
        label="다음"
        :disable="nextDisabled"
        @click="emit('next')"
      />
      <q-btn
        :outline="isDarkNav"
        :unelevated="!isDarkNav"
        no-caps
        class="col"
        :size="navBtnSize"
        :color="prevBtnColor"
        :text-color="prevBtnTextColor"
        label="이전"
        :disable="prevDisabled"
        @click="emit('prev')"
      />
    </template>
  </q-toolbar>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useQuasar } from 'quasar';
import { storeToRefs } from 'pinia';
import { useExamUserOptionsStore } from 'stores/exam-user-options';

defineProps<{
  prevDisabled: boolean;
  nextDisabled: boolean;
}>();

const emit = defineEmits<{
  prev: [];
  next: [];
}>();

const $q = useQuasar();
const isDarkNav = computed(() => $q.dark.isActive);

const prevBtnColor = computed(() => (isDarkNav.value ? 'grey-5' : 'grey-3'));
const prevBtnTextColor = computed(() => (isDarkNav.value ? 'grey-2' : 'grey-9'));

const examUserOpts = useExamUserOptionsStore();
const { stickyButtonHeight, stickyButtonOrder } = storeToRefs(examUserOpts);

const stickyToolbarHeightClass = computed(
  () => `exam-page-sticky-toolbar--${stickyButtonHeight.value}`,
);

/** 시험 옵션의 하단 버튼 영역 높이와 맞춤 (Quasar QBtn size) */
const navBtnSize = computed(() => {
  switch (stickyButtonHeight.value) {
    case 'large':
      return 'lg' as const;
    case 'xlarge':
      return 'xl' as const;
    default:
      return 'md' as const;
  }
});
</script>

<style scoped>
.exam-sheet-nav-toolbar-inner {
  box-shadow: none !important;
  background-color: transparent !important;
  padding-left: 12px !important;
  padding-right: 12px !important;
  gap: 10px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
}
</style>
