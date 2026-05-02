<script setup lang="ts">
import type { Article, ArticleComment, SquareArticle } from '@/types/article'

type Props = {
  article: Article
  stats?: SquareArticle
  comments: ArticleComment[]
  commentText: string
  decayValue: number
}

defineProps<Props>()

const emit = defineEmits<{
  edit: [id: string]
  delete: [id: string]
  loadComments: [id: string]
  submitComment: [id: string]
  deleteComment: [articleId: string, commentId: string]
  updateCommentText: [articleId: string, value: string]
}>()
</script>

<template>
  <article class="mono-panel mb-4">
    <div class="mb-2 flex items-center justify-between gap-2">
      <h3 class="text-xl font-semibold text-black">{{ article.title }}</h3>
      <div class="flex items-center gap-2">
        <button class="mono-btn-primary" @click="emit('edit', article.id)">编辑</button>
        <button class="mono-btn" @click="emit('delete', article.id)">删除</button>
      </div>
    </div>

    <p class="mb-2 text-sm text-neutral-600">{{ article.author }} · {{ article.created_at }}</p>

    <div class="mb-3 flex flex-wrap gap-2">
      <span
        v-for="tag in article.tags"
        :key="tag.id"
        class="border border-black px-2 py-0.5 text-xs text-black"
      >
        {{ tag.name }}
      </span>
    </div>

    <div v-if="stats" class="mb-3 space-y-1 border-y border-black py-2 text-sm text-black">
      <p>当前算法热度：{{ (stats.recommend_reason?.hot_score || 0).toFixed(4) }}</p>
      <p>推荐总分：{{ (stats.recommend_score || 0).toFixed(4) }}</p>
      <p>时间衰减度（0.95^days）：{{ decayValue.toFixed(6) }}</p>
      <p>
        算法分解：相似度{{ (stats.recommend_reason?.similarity_score || 0).toFixed(4) }} /
        关注加成{{ (stats.recommend_reason?.follow_bonus || 0).toFixed(2) }} /
        点赞偏好{{ (stats.recommend_reason?.liked_bonus || 0).toFixed(2) }} /
        多样性惩罚{{ (stats.recommend_reason?.diversity_penalty || 0).toFixed(2) }}
      </p>
    </div>

    <div class="mb-2">
      <button class="mono-btn" @click="emit('loadComments', article.id)">查看评论</button>
    </div>

    <div class="mb-2 flex gap-2">
      <input
        :value="commentText"
        class="flex-1 border border-black px-3 py-2 text-sm outline-none"
        placeholder="写评论并发布"
        @input="emit('updateCommentText', article.id, ($event.target as HTMLInputElement).value)"
      />
      <button class="mono-btn" @click="emit('submitComment', article.id)">发布评论</button>
    </div>

    <div v-if="comments.length" class="space-y-2 border-t border-black pt-2">
      <div
        v-for="comment in comments"
        :key="comment.id"
        class="flex items-center justify-between gap-3 text-sm"
      >
        <span><strong>{{ comment.username }}</strong>：{{ comment.content }}</span>
        <button class="mono-btn" @click="emit('deleteComment', article.id, comment.id)">删除评论</button>
      </div>
    </div>
  </article>
</template>
