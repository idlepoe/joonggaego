<template>
  <q-dialog ref="dialogRef" persistent @hide="onDialogHide">
    <q-card class="q-pa-sm" style="min-width: 300px">
      <q-card-section class="text-body2">
        풀지 않은 문제가 있습니다. 해당 문제로 이동하시겠습니까?
      </q-card-section>
      <q-card-actions align="right" class="q-px-sm q-pb-sm">
        <q-btn flat no-caps color="grey-8" label="취소" @click="onCancelClick" />
        <q-btn outline no-caps color="primary" label="채점" @click="onScoreClick" />
        <q-btn unelevated no-caps color="primary" label="예" @click="onYesClick" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';

const props = defineProps<{
  onYes?: () => void;
  onScore?: () => void;
  onCancel?: () => void;
}>();

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();

function onYesClick() {
  props.onYes?.();
  onDialogOK();
}

function onScoreClick() {
  props.onScore?.();
  onDialogOK();
}

function onCancelClick() {
  props.onCancel?.();
  onDialogCancel();
}
</script>
