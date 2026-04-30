<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useArticle } from '@/composables/useArticle'
import ArticleCard from '@/components/ArticleCard.vue'
import AppDialog from '@/components/AppDialog.vue'
import EmptyWiltedFlower from '@/components/EmptyWiltedFlower.vue'
import AppToast from '@/components/AppToast.vue'

const router = useRouter()
const { articles, loading, error, fetchArticles, deleteArticle } = useArticle()
const deleteId = ref<string | null>(null)
const showDeleteDialog = ref(false)
const showToast = ref(false)
const toastMessage = ref('')

onMounted(() => {
  fetchArticles()
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

function handleEdit(id: string) {
  router.push(`/articles/${id}/edit`)
}

async function handleDelete(id: string) {
  deleteId.value = id
  showDeleteDialog.value = true
}

async function confirmDelete() {
  if (deleteId.value === null) return
  await deleteArticle(deleteId.value)
  deleteId.value = null
  await fetchArticles()
}

function handleCreate() {
  router.push('/articles/create')
}
</script>

<template>
  <div class="articles-view">
    <div class="header">
      <h1>文章列表</h1>
      <button @click="handleCreate" class="btn-create">新建文章</button>
    </div>
    
    <div v-if="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <ArticleCard
        v-for="article in articles"
        :key="article.id"
        :article="article"
        @edit="handleEdit"
        @delete="handleDelete"
      />
      <EmptyWiltedFlower v-if="articles.length === 0" text="暂无文章" />
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

<style scoped>
.articles-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

h1 {
  color: #000000;
}

.btn-create {
  padding: 8px 16px;
  background: #000000;
  color: #ffffff;
  border: 1px solid #000000;
  cursor: pointer;
}

.error {
  color: #000000;
}

</style>
