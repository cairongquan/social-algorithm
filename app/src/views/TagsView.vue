<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useTag } from '@/composables/useTag'
import type { Tag } from '@/types/tag'
import AppDialog from '@/components/AppDialog.vue'
import AppInput from '@/components/AppInput.vue'
import EmptyWiltedFlower from '@/components/EmptyWiltedFlower.vue'

const { tags, pushPreview, loading, error, fetchTags, createTag, updateTag, deleteTag, fetchPushPreview } = useTag()

const newTagName = ref('')
const editingTag = ref<Tag | null>(null)
const editingName = ref('')
const showInfoDialog = ref(false)
const showDeleteDialog = ref(false)
const dialogTitle = ref('')
const dialogMessage = ref('')
const pendingDeleteId = ref<string | null>(null)
let previewTimer: number | undefined

onMounted(() => {
  fetchTags()
})

watch(newTagName, (value) => {
  window.clearTimeout(previewTimer)
  previewTimer = window.setTimeout(() => {
    fetchPushPreview(value)
  }, 300)
})

async function handleCreate() {
  if (!newTagName.value.trim()) return
  try {
    await createTag({ name: newTagName.value })
    newTagName.value = ''
  } catch (err) {
    dialogTitle.value = '创建失败'
    dialogMessage.value = '创建标签失败，请稍后重试。'
    showInfoDialog.value = true
  }
}

function startEdit(tag: Tag) {
  editingTag.value = tag
  editingName.value = tag.name
}

async function handleUpdate() {
  if (!editingTag.value || !editingName.value.trim()) return
  try {
    await updateTag(editingTag.value.id, { name: editingName.value })
    editingTag.value = null
    editingName.value = ''
  } catch (err) {
    dialogTitle.value = '更新失败'
    dialogMessage.value = '更新标签失败，请稍后重试。'
    showInfoDialog.value = true
  }
}

async function handleDelete(id: string) {
  pendingDeleteId.value = id
  showDeleteDialog.value = true
}

async function confirmDelete() {
  if (pendingDeleteId.value === null) return
  try {
    await deleteTag(pendingDeleteId.value)
    pendingDeleteId.value = null
  } catch (err) {
    dialogTitle.value = '删除失败'
    dialogMessage.value = '删除标签失败，请稍后重试。'
    showInfoDialog.value = true
  }
}
</script>

<template>
  <div class="tags-view">
    <h1>标签管理</h1>
    
    <div v-if="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="create-form">
        <AppInput v-model="newTagName" type="text" placeholder="请输入标签名称" />
        <button @click="handleCreate" class="btn-create">新增</button>
      </div>

      <div v-if="pushPreview && pushPreview.candidates.length > 0" class="push-preview">
        <h2>可能会推送的用户</h2>
        <p class="preview-subtitle">标签：{{ pushPreview.tag_name }}</p>
        <div class="candidate-list">
          <div v-for="candidate in pushPreview.candidates" :key="candidate.user_id" class="candidate-card">
            <div class="candidate-head">
              <img
                v-if="candidate.avatar_url"
                :src="candidate.avatar_url"
                :alt="candidate.username"
                class="avatar"
              />
              <div v-else class="avatar fallback">{{ candidate.username.slice(0, 1) }}</div>
              <div>
                <div class="username">{{ candidate.username }}</div>
                <div class="discipline">{{ candidate.push_discipline }}</div>
              </div>
            </div>
            <div class="reason">{{ candidate.reason }}</div>
            <div class="score">推荐分：{{ candidate.score.toFixed(4) }}</div>
          </div>
        </div>
      </div>
      
      <table v-if="tags.length > 0" class="tags-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>关联文章数</th>
            <th>涉及用户数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tag in tags" :key="tag.id">
            <td>{{ tag.id }}</td>
            <td v-if="editingTag?.id !== tag.id">{{ tag.name }}</td>
            <td v-else>
              <AppInput v-model="editingName" type="text" />
              <button @click="handleUpdate" class="btn-save">保存</button>
              <button @click="editingTag = null" class="btn-cancel">取消</button>
            </td>
            <td>{{ tag.article_count ?? 0 }}</td>
            <td>{{ tag.related_user_count ?? 0 }}</td>
            <td>
              <button v-if="editingTag?.id !== tag.id" @click="startEdit(tag)" class="btn-edit">编辑</button>
              <button @click="handleDelete(tag.id)" class="btn-delete">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <EmptyWiltedFlower v-else text="暂无标签" />
    </div>
  </div>
  <AppDialog
    v-model="showInfoDialog"
    :title="dialogTitle"
    :message="dialogMessage"
    confirm-text="我知道了"
  />
  <AppDialog
    v-model="showDeleteDialog"
    title="删除标签"
    message="确认删除该标签吗？删除后将清除关联文章中的该标签。"
    :show-cancel="true"
    confirm-text="确认删除"
    cancel-text="取消"
    @confirm="confirmDelete"
  />
</template>

<style scoped>
.tags-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px;
}

h1 {
  color: #000000;
}

.create-form {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}

.create-form :deep(.app-input) {
  flex: 1;
}

.push-preview {
  border: 1px solid #000000;
  padding: 16px;
  margin-bottom: 24px;
}

.push-preview h2 {
  margin: 0;
  font-size: 20px;
}

.preview-subtitle {
  margin-top: 6px;
  margin-bottom: 14px;
  color: #333333;
}

.candidate-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.candidate-card {
  border: 1px solid #000000;
  padding: 12px;
}

.candidate-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.avatar {
  width: 44px;
  height: 44px;
  object-fit: cover;
  border: 1px solid #000000;
}

.avatar.fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000000;
  color: #ffffff;
}

.username {
  font-weight: 600;
}

.discipline {
  font-size: 13px;
  color: #333333;
}

.reason {
  font-size: 14px;
  margin-bottom: 6px;
}

.score {
  font-size: 13px;
  color: #333333;
}

.tags-table {
  width: 100%;
  border-collapse: collapse;
}

.tags-table th, .tags-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #000000;
}

.tags-table th {
  background: #ffffff;
}

.btn-create, .btn-save {
  padding: 8px 16px;
  background: #000000;
  color: #ffffff;
  border: 1px solid #000000;
  cursor: pointer;
}

.btn-edit {
  padding: 6px 12px;
  background: #000000;
  color: #ffffff;
  border: 1px solid #000000;
  cursor: pointer;
  margin-right: 4px;
}

.btn-delete {
  padding: 6px 12px;
  background: #ffffff;
  color: #000000;
  border: 1px solid #000000;
  cursor: pointer;
}

.btn-cancel {
  padding: 6px 12px;
  background: #ffffff;
  color: #000000;
  border: 1px solid #000000;
  cursor: pointer;
}

.error {
  color: #000000;
}
</style>
