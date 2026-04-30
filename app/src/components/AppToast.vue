<script setup lang="ts">
interface Props {
  modelValue: boolean
  message: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <Teleport to="body">
    <div v-if="props.modelValue" class="toast-wrap">
      <div class="toast">
        <span>{{ props.message }}</span>
        <button class="toast-close" @click="close">×</button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-wrap {
  position: fixed;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1200;
}

.toast {
  min-width: 220px;
  max-width: 80vw;
  border: 1px solid #000000;
  background: #ffffff;
  color: #000000;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.toast-close {
  border: 1px solid #000000;
  background: #ffffff;
  color: #000000;
  width: 22px;
  height: 22px;
  line-height: 18px;
  cursor: pointer;
}
</style>
