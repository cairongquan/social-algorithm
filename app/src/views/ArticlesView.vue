<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useArticle } from '@/composables/useArticle'
import { useAuthStore } from '@/stores/auth'
import { articlesApi } from '@/api/articles'
import type { SquareArticle, ArticleComment } from '@/types/article'
import MyArticlePanel from '@/components/MyArticlePanel.vue'
import AppDialog from '@/components/AppDialog.vue'
import EmptyWiltedFlower from '@/components/EmptyWiltedFlower.vue'
import AppToast from '@/components/AppToast.vue'

const router = useRouter()
const authStore = useAuthStore()
const { articles, loading, error, fetchArticles, deleteArticle } = useArticle()

const mySquareArticles = ref<SquareArticle[]>([])
const commentsMap = ref<Record<string, ArticleComment[]>>({})
const commentInput = ref<Record<string, string>>({})
const deleteId = ref<string | null>(null)
const showDeleteDialog = ref(false)
const showToast = ref(false)
const toastMessage = ref('')

const myArticles = computed(() => {
  if (authStore.isAdmin) {
    return articles.value
  }
  const username = authStore.username || ''
  return articles.value.filter((item) => item.author === username)
})

onMounted(async () => {
  await loadMine()
  const flash = localStorage.getItem('flash_toast')
  if (flash) {
    toastMessage.value = flash
    showToast.value = true
    localStorage.removeItem('flash_toast')
    window.setTimeout(() => {
      showToast.value = false
    }, 1800)
  }
})

async function loadMine() {
  await fetchArticles()
  const square = await articlesApi.square()
  mySquareArticles.value = square.filter((item) => item.author === (authStore.username || ''))
}

function handleEdit(id: string) {
  router.push(`/articles/${id}/edit`)
}

function handleDelete(id: string) {
  deleteId.value = id
  showDeleteDialog.value = true
}

async function confirmDelete() {
  if (deleteId.value === null) return
  await deleteArticle(deleteId.value)
  deleteId.value = null
  await loadMine()
}

function handleCreate() {
  router.push('/articles/create')
}

function getStats(articleId: string): SquareArticle | undefined {
  return mySquareArticles.value.find((item) => item.id === articleId)
}

function decayByDays(createdAt: string): number {
  const created = new Date(createdAt)
  const now = new Date()
  const days = Math.max(0, Math.floor((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24)))
  return Math.pow(0.95, days)
}

async function loadComments(articleId: string) {
  if (commentsMap.value[articleId]) return
  commentsMap.value = {
    ...commentsMap.value,
    [articleId]: await articlesApi.comments(articleId)
  }
}

async function submitComment(articleId: string) {
  const content = (commentInput.value[articleId] || '').trim()
  if (!content) {
    toastMessage.value = '评论内容不能为空'
    showToast.value = true
    return
  }
  const created = await articlesApi.addComment(articleId, content)
  const list = commentsMap.value[articleId] || []
  commentsMap.value = { ...commentsMap.value, [articleId]: [created, ...list] }
  commentInput.value = { ...commentInput.value, [articleId]: '' }
  await loadMine()
}

async function removeComment(articleId: string, commentId: string) {
  await articlesApi.deleteComment(articleId, commentId)
  const list = commentsMap.value[articleId] || []
  commentsMap.value = {
    ...commentsMap.value,
    [articleId]: list.filter((item) => item.id !== commentId)
  }
  await loadMine()
}
</script>

<template>
  <div class="mx-auto max-w-5xl px-8 py-8">
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-3xl font-semibold text-black">{{ authStore.isAdmin ? '全部用户文章' : '我的文章' }}</h1>
      <button @click="handleCreate" class="mono-btn-primary">新建文章</button>
    </div>

    <div v-if="loading">加载中...</div>
    <div v-else-if="error" class="text-black">{{ error }}</div>
    <div v-else>
      <MyArticlePanel
        v-for="article in myArticles"
        :key="article.id"
        :article="article"
        :stats="getStats(article.id)"
        :comments="commentsMap[article.id] || []"
        :comment-text="commentInput[article.id] || ''"
        :decay-value="decayByDays(article.created_at)"
        @edit="handleEdit"
        @delete="handleDelete"
        @load-comments="loadComments"
        @submit-comment="submitComment"
        @delete-comment="removeComment"
        @update-comment-text="(articleId, value) => { commentInput[articleId] = value }"
      />

      <EmptyWiltedFlower v-if="myArticles.length === 0" text="你还没有创建文章" />
    </div>
  </div>

  <AppDialog
    v-model="showDeleteDialog"
    title="删除文章"
    message="确认删除这篇文章吗？此操作不可恢复。"
    :show-cancel="true"
    confirm-text="确认删除"
    cancel-text="取消"
    @confirm="confirmDelete"
  />
  <AppToast v-model="showToast" :message="toastMessage" />
</template>
