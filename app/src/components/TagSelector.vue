<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { tagsApi } from '@/api/tags'
import type { Tag } from '@/types/tag'

interface Props {
  modelValue: string[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const tags = ref<Tag[]>([])
const selectedTags = ref<string[]>(props.modelValue)

watch(
  () => props.modelValue,
  (value) => {
    selectedTags.value = [...value]
  },
  { immediate: true }
)

onMounted(async () => {
  try {
    tags.value = await tagsApi.list()
  } catch (error) {
    console.error('Failed to fetch tags', error)
  }
})

function toggleTag(tagId: string) {
  const index = selectedTags.value.indexOf(tagId)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tagId)
  }
  emit('update:modelValue', [...selectedTags.value])
}
</script>

<template>
  <div class="tag-selector">
    <div v-for="tag in tags" :key="tag.id" 
         :class="['tag-item', { selected: selectedTags.includes(tag.id) }]"
         @click="toggleTag(tag.id)">
      {{ tag.name }}
    </div>
  </div>
</template>

<style scoped>
.tag-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0;
}

.tag-item {
  padding: 8px 12px;
  border: 1px solid #000000;
  border-radius: 0;
  cursor: pointer;
  color: #000000;
  background: #ffffff;
}

.tag-item.selected {
  background: #000000;
  color: #ffffff;
}
</style>
