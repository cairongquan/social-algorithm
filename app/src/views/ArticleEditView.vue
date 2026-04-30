<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useArticle } from '@/composables/useArticle'
import { useTag } from '@/composables/useTag'
import TinyEditor from '@/components/TinyEditor.vue'
import TagSelector from '@/components/TagSelector.vue'
import AppDialog from '@/components/AppDialog.vue'
import AppInput from '@/components/AppInput.vue'

const router = useRouter()
const route = useRoute()
const { article, loading, error, fetchArticle, createArticle, updateArticle } = useArticle()
const { fetchTags } = useTag()

const title = ref('')
const content = ref('')
const selectedTagIds = ref<string[]>([])
const showDialog = ref(false)
const dialogTitle = ref('')
const dialogMessage = ref('')

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
</style>
