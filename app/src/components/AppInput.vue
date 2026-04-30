<script setup lang="ts">
interface Props {
  modelValue: string
  type?: string
  placeholder?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  placeholder: '',
  disabled: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

function onInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <input
    :value="props.modelValue"
    :type="props.type"
    :placeholder="props.placeholder"
    :disabled="props.disabled"
    class="app-input"
    @input="onInput"
  />
</template>

<style scoped>
.app-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #000000;
  box-sizing: border-box;
  background: #ffffff;
  color: #000000;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
  border-radius: 0;
}

.app-input:hover,
.app-input:active,
.app-input:focus {
  border: 1px solid #000000;
  box-shadow: none;
}

.app-input:disabled {
  background: #f2f2f2;
  color: #666666;
}
</style>
