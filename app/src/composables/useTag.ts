import { ref } from 'vue'
import { tagsApi } from '@/api/tags'
import type { Tag, TagCreate, TagUpdate, TagPushPreview } from '@/types/tag'

export function useTag() {
  const tags = ref<Tag[]>([])
  const pushPreview = ref<TagPushPreview | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchTags() {
    loading.value = true
    error.value = null
    try {
      tags.value = await tagsApi.list()
    } catch (err) {
      error.value = '获取标签失败'
    } finally {
      loading.value = false
    }
  }

  async function createTag(data: TagCreate) {
    loading.value = true
    error.value = null
    try {
      await tagsApi.create(data)
      await fetchTags()
    } catch (err) {
      error.value = '创建标签失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateTag(id: string, data: TagUpdate) {
    loading.value = true
    error.value = null
    try {
      await tagsApi.update(id, data)
      await fetchTags()
    } catch (err) {
      error.value = '更新标签失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteTag(id: string) {
    loading.value = true
    error.value = null
    try {
      await tagsApi.delete(id)
      await fetchTags()
    } catch (err) {
      error.value = '删除标签失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchPushPreview(name: string) {
    const tagName = name.trim()
    if (!tagName) {
      pushPreview.value = null
      return
    }
    try {
      pushPreview.value = await tagsApi.previewPushUsers(tagName)
    } catch (err) {
      pushPreview.value = null
    }
  }

  return { tags, pushPreview, loading, error, fetchTags, createTag, updateTag, deleteTag, fetchPushPreview }
}
