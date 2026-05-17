<template>
  <div class="app-root">
    <ExamAppIntroRail class="app-intro-rail" />
    <div id="app-shell">
      <router-view />
    </div>
  </div>
</template>
<script setup lang="ts">
import ExamAppIntroRail from 'src/components/exam/ExamAppIntroRail.vue';
</script>
