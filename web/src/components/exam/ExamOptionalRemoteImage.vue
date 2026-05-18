<template>
  <div v-if="show" class="exam-optional-remote-img" :class="{ 'q-mb-lg': bottomSpacing }">
    <img :src="src" alt="" loading="lazy" @error="show = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = withDefaults(
  defineProps<{
    src: string;
    /** 이미지가 표시될 때 하단 여백(문항 이미지용) */
    bottomSpacing?: boolean;
  }>(),
  { bottomSpacing: false },
);

const show = ref(true);

watch(
  () => props.src,
  () => {
    show.value = true;
  },
);
</script>

<style scoped>
.exam-optional-remote-img {
  line-height: 0;
}
.exam-optional-remote-img img {
  max-width: 100%;
  height: auto;
  vertical-align: top;
}
</style>
