<template>
  <q-layout view="lHh Lpr lFf" class="fit">
    <q-header class="bg-primary text-white">
      <q-toolbar class="items-start q-py-sm">
        <q-btn
          v-if="showBack"
          flat
          round
          dense
          icon="arrow_back"
          class="q-mt-xs"
          aria-label="뒤로가기"
          @click="goBack"
        />
        <q-toolbar-title class="text-body1 text-weight-medium">
          <div
            v-if="route.name === 'exam-sheet' || route.name === 'exam-mock-review'"
            class="column text-caption text-weight-medium"
            style="line-height: 1.35"
          >
            <div class="ellipsis">{{ sheetToolbar.line1 || '\u00a0' }}</div>
            <div>{{ sheetToolbar.line2 || '\u00a0' }}</div>
          </div>
          <div
            v-else-if="route.name === 'exam-mock'"
            class="column full-width text-caption text-weight-medium"
            style="line-height: 1.35"
          >
            <div class="ellipsis">{{ mockToolbar.line1 || '\u00a0' }}</div>
            <div>{{ mockToolbar.line2 || '\u00a0' }}</div>
            <div class="row items-center no-wrap q-mt-xs q-gutter-x-xs">
              <div class="col ellipsis">{{ mockToolbar.timerLabel }}</div>
              <q-btn
                dense
                flat
                no-caps
                color="white"
                class="no-shrink"
                label="답안제출"
                @click="mockToolbar.requestSubmit()"
              />
              <q-btn
                dense
                flat
                no-caps
                color="white"
                class="no-shrink"
                label="답안 확인"
                @click="mockToolbar.requestAnswerReview()"
              />
            </div>
          </div>
          <div v-else-if="route.name === 'exam-main'" class="row items-center no-wrap full-width">
            <span class="ellipsis col">{{ toolbarTitle }}</span>
            <q-btn
              flat
              round
              dense
              icon="settings"
              class="no-shrink"
              aria-label="설정"
              @click="goOptions"
            />
          </div>
          <span v-else>{{ toolbarTitle }}</span>
        </q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useExamSheetToolbarStore } from 'stores/exam-sheet-toolbar';
import { useMockExamToolbarStore } from 'stores/mock-exam-toolbar';

const route = useRoute();
const router = useRouter();
const sheetToolbar = useExamSheetToolbarStore();
const mockToolbar = useMockExamToolbarStore();

const showBack = computed(
  () =>
    route.name === 'exam-sessions' ||
    route.name === 'exam-sheet' ||
    route.name === 'exam-mock' ||
    route.name === 'exam-mock-review' ||
    route.name === 'exam-options',
);

const toolbarTitle = computed(() => {
  if (route.name === 'exam-main') {
    return '광고없는주택관리사1차기출회독';
  }
  if (route.name === 'exam-options') {
    return '설정';
  }
  if (route.name === 'exam-sessions') {
    const subject = String(route.params.subject ?? '');
    return `회독 ${subject}`;
  }
  return '';
});

function goOptions() {
  void router.push({ name: 'exam-options' });
}

function goBack() {
  if (route.name === 'exam-options') {
    void router.push({ name: 'exam-main' });
    return;
  }
  if (route.name === 'exam-sessions') {
    void router.push({ name: 'exam-main' });
    return;
  }
  if (route.name === 'exam-sheet') {
    const subject = String(route.params.subject ?? '');
    void router.push({ name: 'exam-sessions', params: { subject } });
    return;
  }
  if (route.name === 'exam-mock') {
    void router.push({ name: 'exam-main' });
    return;
  }
  if (route.name === 'exam-mock-review') {
    void router.push({ name: 'exam-main' });
    return;
  }
}
</script>

<style scoped>
.no-shrink {
  flex-shrink: 0;
}
</style>
