<template>
  <div v-if="show" class="exam-optional-remote-img">
    <img :src="src" alt="" loading="lazy" @error="show = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  src: string;
}>();

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
