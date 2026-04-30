<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import Quill from 'quill'
import 'quill/dist/quill.snow.css'

interface Props {
  modelValue: string
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  height: 500
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const editorRef = ref<HTMLElement | null>(null)
let quill: Quill | null = null
let isSyncingFromEditor = false

async function uploadImage(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch('/api/v1/uploads/upload', {
    method: 'POST',
    body: formData,
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`
    }
  })
  if (!response.ok) {
    throw new Error('上传图片失败')
  }
  const data = await response.json()
  return data.url
}

async function handleImage() {
  const input = document.createElement('input')
  input.setAttribute('type', 'file')
  input.setAttribute('accept', 'image/*')
  input.click()

  input.onchange = async () => {
    const file = input.files?.[0]
    if (!file) return
    const imageUrl = await uploadImage(file)
    if (!quill) return
    const range = quill.getSelection(true)
    const index = range?.index ?? quill.getLength()
    quill.insertEmbed(index, 'image', imageUrl)
    quill.setSelection(index + 1)
  }
}

const toolbarOptions = [
  ['bold', 'italic', 'underline', 'strike'],
  [{ header: 1 }, { header: 2 }],
  [{ list: 'ordered' }, { list: 'bullet' }],
  [{ indent: '-1' }, { indent: '+1' }],
  [{ align: [] }],
  ['link', 'image'],
  ['clean']
]

onMounted(() => {
  if (!editorRef.value) return
  quill = new Quill(editorRef.value, {
    theme: 'snow',
    modules: {
      toolbar: {
        container: toolbarOptions,
        handlers: {
          image: handleImage
        }
      }
    }
  })

  if (props.modelValue) {
    quill.root.innerHTML = props.modelValue
  }

  quill.on('text-change', () => {
    if (!quill) return
    isSyncingFromEditor = true
    emit('update:modelValue', quill.root.innerHTML)
    isSyncingFromEditor = false
  })
})

watch(
  () => props.modelValue,
  (val) => {
    if (!quill || isSyncingFromEditor) return
    const next = val || ''
    if (quill.root.innerHTML !== next) {
      quill.root.innerHTML = next
    }
  }
)

onBeforeUnmount(() => {
  quill = null
})
</script>

<template>
  <div class="tiny-editor" :style="{ minHeight: `${props.height}px` }">
    <div ref="editorRef" />
  </div>
</template>

<style scoped>
.tiny-editor {
  border: 1px solid #000000;
  margin: 16px 0;
  background: #ffffff;
}

.tiny-editor :deep(.ql-toolbar) {
  border: 0;
  border-bottom: 1px solid #000000;
}

.tiny-editor :deep(.ql-container) {
  border: 0;
  font-family: "Source Serif 4", Georgia, serif;
  min-height: 360px;
}

.tiny-editor :deep(.ql-editor) {
  min-height: 320px;
}
</style>
