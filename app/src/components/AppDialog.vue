<script setup lang="ts">
interface Props {
  modelValue: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  showCancel?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  confirmText: '确定',
  cancelText: '取消',
  showCancel: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
  cancel: []
}>()

function close() {
  emit('update:modelValue', false)
}

function onConfirm() {
  emit('confirm')
  close()
}

function onCancel() {
  emit('cancel')
  close()
}
</script>

<template>
  <Teleport to="body">
    <div v-if="props.modelValue" class="dialog-overlay" @click.self="onCancel">
      <div class="dialog-panel" role="dialog" aria-modal="true">
        <h3 class="dialog-title">{{ props.title }}</h3>
        <p class="dialog-message">{{ props.message }}</p>
        <div class="dialog-actions">
          <button v-if="props.showCancel" class="btn-cancel" @click="onCancel">
            {{ props.cancelText }}
          </button>
          <button class="btn-confirm" @click="onConfirm">
            {{ props.confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-panel {
  width: min(92vw, 460px);
  background: #ffffff;
  border: 2px solid #000000;
  padding: 20px;
}

.dialog-title {
  margin: 0 0 10px 0;
  font-size: 22px;
  color: #000000;
}

.dialog-message {
  margin: 0;
  color: #000000;
  line-height: 1.6;
}

.dialog-actions {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-cancel,
.btn-confirm {
  padding: 8px 14px;
  border: 1px solid #000000;
  cursor: pointer;
}

.btn-cancel {
  background: #ffffff;
  color: #000000;
}

.btn-confirm {
  background: #000000;
  color: #ffffff;
}
</style>
