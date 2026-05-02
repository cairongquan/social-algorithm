<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useArticle } from '@/composables/useArticle'
import { useTag } from '@/composables/useTag'
import { tagsApi } from '@/api/tags'
import TinyEditor from '@/components/TinyEditor.vue'
import TagSelector from '@/components/TagSelector.vue'
import AppDialog from '@/components/AppDialog.vue'
import AppInput from '@/components/AppInput.vue'
import type { TagPushCandidate } from '@/types/tag'

const router = useRouter()
const route = useRoute()
const { article, loading, error, fetchArticle, createArticle, updateArticle } = useArticle()
const { tags, fetchTags } = useTag()

const title = ref('')
const content = ref('')
const selectedTagIds = ref<string[]>([])
const showDialog = ref(false)
const dialogTitle = ref('')
const dialogMessage = ref('')
const pushCandidates = ref<Array<TagPushCandidate & { matched_tags: string[] }>>([])
const previewLoading = ref(false)
let previewTimer: number | undefined

const isEdit = route.params.id !== undefined
const articleId = isEdit ? String(route.params.id) : null

onMounted(async () => {
  await fetchTags()
  if (isEdit && articleId) {
    await fetchArticle(articleId)
    if (article.value) {
      title.value = article.value.title
      content.value = article.value.content
      selectedTagIds.value = article.value.tags.map(t => t.id)
    }
  }
})

watch(
  selectedTagIds,
  () => {
    window.clearTimeout(previewTimer)
    previewTimer = window.setTimeout(() => {
      refreshPushCandidates()
    }, 250)
  },
  { deep: true }
)

async function refreshPushCandidates() {
  const selectedNames = tags.value
    .filter((tag) => selectedTagIds.value.includes(tag.id))
    .map((tag) => tag.name)

  if (selectedNames.length === 0) {
    pushCandidates.value = []
    return
  }

  previewLoading.value = true
  try {
    const previews = await Promise.all(selectedNames.map((name) => tagsApi.previewPushUsers(name)))
    const merged = new Map<string, TagPushCandidate & { matched_tags: string[] }>()

    previews.forEach((preview) => {
      preview.candidates.forEach((candidate) => {
        const found = merged.get(candidate.user_id)
        if (!found) {
          merged.set(candidate.user_id, {
            ...candidate,
            matched_tags: [preview.tag_name]
          })
          return
        }

        const nextMatched = found.matched_tags.includes(preview.tag_name)
          ? found.matched_tags
          : [...found.matched_tags, preview.tag_name]
        const nextScore = Math.max(found.score, candidate.score)
        const nextDiscipline = nextScore >= found.score ? candidate.push_discipline : found.push_discipline
        const nextReason = nextScore >= found.score ? candidate.reason : found.reason

        merged.set(candidate.user_id, {
          ...found,
          score: nextScore,
          push_discipline: nextDiscipline,
          reason: nextReason,
          matched_tags: nextMatched
        })
      })
    })

    pushCandidates.value = Array.from(merged.values())
      .sort((a, b) => b.score - a.score)
      .slice(0, 12)
  } catch (err) {
    pushCandidates.value = []
  } finally {
    previewLoading.value = false
  }
}

async function handleSubmit() {
  if (!title.value.trim()) {
    dialogTitle.value = '提示'
    dialogMessage.value = '请输入文章标题'
    showDialog.value = true
    return
  }

  try {
    if (isEdit && articleId) {
      await updateArticle(articleId, {
        title: title.value,
        content: content.value,
        tag_ids: selectedTagIds.value
      })
    } else {
      await createArticle({
        title: title.value,
        content: content.value,
        tag_ids: selectedTagIds.value
      })
      localStorage.setItem('flash_toast', '文章创建成功')
      router.push('/')
      return
    }
    router.push('/')
  } catch (err) {
    dialogTitle.value = '保存失败'
    dialogMessage.value = '保存文章失败，请稍后重试。'
    showDialog.value = true
  }
}
</script>

<template>
  <div class="article-edit-view">
    <h1>{{ isEdit ? '编辑文章' : '创建文章' }}</h1>
    
    <div v-if="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="form-group">
        <label>文章标题</label>
        <AppInput v-model="title" type="text" placeholder="请输入文章标题" />
      </div>
      
      <div class="form-group">
        <label>关联标签</label>
        <TagSelector v-model="selectedTagIds" />
      </div>

      <div v-if="selectedTagIds.length > 0" class="push-preview">
        <div class="preview-title">可能会推送的用户</div>
        <div v-if="previewLoading" class="preview-subtitle">正在根据已选标签计算...</div>
        <div v-else-if="pushCandidates.length === 0" class="preview-subtitle">暂无可推荐用户</div>
        <div v-else class="candidate-list">
          <div v-for="candidate in pushCandidates" :key="candidate.user_id" class="candidate-card">
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
            <div class="hit-tags">命中标签：{{ candidate.matched_tags.join('、') }}</div>
            <div class="reason">{{ candidate.reason }}</div>
            <div class="score">推荐分：{{ candidate.score.toFixed(4) }}</div>
          </div>
        </div>
      </div>
      
      <div class="form-group">
        <label>文章内容</label>
        <TinyEditor v-model="content" />
      </div>
      
      <button @click="handleSubmit" class="btn-submit">
        {{ isEdit ? '更新' : '创建' }}
      </button>
      <button @click="router.push('/')" class="btn-cancel">取消</button>
    </div>
  </div>
  <AppDialog
    v-model="showDialog"
    :title="dialogTitle"
    :message="dialogMessage"
    confirm-text="我知道了"
  />
</template>

<style scoped>
.article-edit-view {
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px;
}

h1 {
  color: #000000;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 4px;
  color: #333;
}

.btn-submit {
  padding: 10px 20px;
  background: #000000;
  color: #ffffff;
  border: 1px solid #000000;
  cursor: pointer;
  margin-right: 8px;
}

.btn-cancel {
  padding: 10px 20px;
  background: #ffffff;
  color: #000000;
  border: 1px solid #000000;
  cursor: pointer;
}

.error {
  color: #000000;
  margin: 16px 0;
}

.push-preview {
  border: 1px solid #000000;
  padding: 14px;
  margin-bottom: 16px;
}

.preview-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 8px;
}

.preview-subtitle {
  color: #333333;
  font-size: 14px;
}

.candidate-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 10px;
}

.candidate-card {
  border: 1px solid #000000;
  padding: 10px;
}

.candidate-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.avatar {
  width: 42px;
  height: 42px;
  border: 1px solid #000000;
  object-fit: cover;
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

.discipline,
.hit-tags,
.reason,
.score {
  font-size: 13px;
  color: #333333;
}

.hit-tags,
.reason {
  margin-bottom: 4px;
}
</style>
