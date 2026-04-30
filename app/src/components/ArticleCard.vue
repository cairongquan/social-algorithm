<script setup lang="ts">
import type { Article } from '@/types/article'

interface Props {
  article: Article
}

defineProps<Props>()

const emit = defineEmits<{
  edit: [id: string]
  delete: [id: string]
}>()
</script>

<template>
  <div class="article-card">
    <h3 class="article-title">{{ article.title }}</h3>
    <div class="article-meta">
      <span class="author">{{ article.author }}</span>
      <span class="date">{{ article.created_at }}</span>
    </div>
    <div class="article-tags">
      <span v-for="tag in article.tags" :key="tag.id" class="tag">{{ tag.name }}</span>
    </div>
    <div class="article-actions">
      <button @click="emit('edit', article.id)" class="btn-edit">编辑</button>
      <button @click="emit('delete', article.id)" class="btn-delete">删除</button>
    </div>
  </div>
</template>

<style scoped>
.article-card {
  border: 1px solid #000000;
  padding: 16px;
  margin: 16px 0;
  background: #fff;
}

.article-title {
  color: #000000;
  margin: 0 0 8px 0;
}

.article-meta {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.author {
  margin-right: 16px;
}

.article-tags {
  margin: 8px 0;
}

.tag {
  display: inline-block;
  background: #000000;
  color: #ffffff;
  padding: 4px 8px;
  border-radius: 0;
  font-size: 12px;
  margin-right: 8px;
}

.article-actions {
  margin-top: 12px;
}

.btn-edit, .btn-delete {
  padding: 6px 12px;
  margin-right: 8px;
  border: 1px solid #000000;
  border-radius: 0;
  cursor: pointer;
}

.btn-edit {
  background: #000000;
  color: #ffffff;
}

.btn-delete {
  background: #ffffff;
  color: #000000;
}
</style>
