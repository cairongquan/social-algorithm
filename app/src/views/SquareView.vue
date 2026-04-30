<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { articlesApi } from '@/api/articles'
import type { SquareArticle, ArticleComment } from '@/types/article'
import AppInput from '@/components/AppInput.vue'
import AppDialog from '@/components/AppDialog.vue'
import EmptyWiltedFlower from '@/components/EmptyWiltedFlower.vue'

const loading = ref(false)
const error = ref('')
const articles = ref<SquareArticle[]>([])
const currentIndex = ref(0)
const commentsMap = ref<Record<string, ArticleComment[]>>({})
const commentInput = ref<Record<string, string>>({})
const swiping = ref(false)
const showDialog = ref(false)
const dialogMessage = ref('')
const showSwipeOverlay = ref(false)

const currentArticle = computed(() => articles.value[currentIndex.value] || null)

let previousBodyOverflow = ''

watch(showSwipeOverlay, (visible) => {
  if (visible) {
    previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = previousBodyOverflow
  }
})

async function loadSquare() {
  loading.value = true
  error.value = ''
  try {
    articles.value = await articlesApi.square()
  } catch (e) {
    error.value = '加载广场失败'
  } finally {
    loading.value = false
  }
}

async function toggleLike(article: SquareArticle) {
  const result = await articlesApi.toggleLike(article.id)
  article.liked_by_me = result.liked
  article.likes_count = result.likes_count
}

async function loadComments(articleId: string) {
  if (commentsMap.value[articleId]) return
  const list = await articlesApi.comments(articleId)
  commentsMap.value = { ...commentsMap.value, [articleId]: list }
}

async function submitComment(articleId: string) {
  const content = (commentInput.value[articleId] || '').trim()
  if (!content) {
    dialogMessage.value = '请输入评论内容'
    showDialog.value = true
    return
  }
  const created = await articlesApi.addComment(articleId, content)
  const existing = commentsMap.value[articleId] || []
  commentsMap.value = { ...commentsMap.value, [articleId]: [created, ...existing] }
  commentInput.value = { ...commentInput.value, [articleId]: '' }
  const hit = articles.value.find(a => a.id === articleId)
  if (hit) hit.comments_count += 1
}

async function openSwipeOverlay(startId: string) {
  const index = articles.value.findIndex(item => item.id === startId)
  currentIndex.value = index >= 0 ? index : 0
  showSwipeOverlay.value = true
  try {
    await articlesApi.markView(startId)
  } catch (error) {
    // ignore behavior logging failure
  }
}

function closeSwipeOverlay() {
  showSwipeOverlay.value = false
  swiping.value = false
}

function prevSwipe() {
  if (currentIndex.value <= 0) return
  swiping.value = true
  window.setTimeout(() => {
    currentIndex.value -= 1
    swiping.value = false
  }, 220)
}

function nextSwipe() {
  if (currentIndex.value >= articles.value.length - 1) return
  swiping.value = true
  window.setTimeout(() => {
    currentIndex.value += 1
    swiping.value = false
    const next = currentArticle.value
    if (next) {
      articlesApi.markView(next.id).catch(() => {})
    }
  }, 220)
}

onMounted(() => {
  loadSquare()
})

onBeforeUnmount(() => {
  document.body.style.overflow = previousBodyOverflow
})
</script>

<template>
  <div class="square-view">
    <div class="header">
      <h1>广场</h1>
      <p class="header-hint">点击卡片进入左滑模式</p>
    </div>

    <div v-if="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <EmptyWiltedFlower v-else-if="articles.length === 0" text="广场暂无内容" />

    <div v-else class="feed-list">
      <article v-for="item in articles" :key="item.id" class="square-card">
        <h3>{{ item.title }}</h3>
        <p class="meta">{{ item.author }} · {{ item.created_at }}</p>
        <div class="content" v-html="item.content"></div>
        <div class="tags">
          <span v-for="tag in item.tags" :key="tag.id" class="tag">{{ tag.name }}</span>
        </div>
        <div class="actions">
          <button class="action-btn" @click.stop="toggleLike(item)">{{ item.liked_by_me ? '取消赞' : '点赞' }} {{ item.likes_count }}</button>
          <button class="action-btn" @click.stop="loadComments(item.id)">评论 {{ item.comments_count }}</button>
          <button class="action-btn" @click.stop="openSwipeOverlay(item.id)">卡片浏览</button>
        </div>
        <div class="comment-box" @click.stop>
          <AppInput v-model="commentInput[item.id]" placeholder="写下你的留言/评论" />
          <button class="action-btn" @click.stop="submitComment(item.id)">发布</button>
        </div>
        <div class="comments" v-if="commentsMap[item.id]?.length" @click.stop>
          <p v-for="comment in commentsMap[item.id]" :key="comment.id" class="comment-line">
            <strong>{{ comment.username }}：</strong>{{ comment.content }}
          </p>
        </div>
      </article>
    </div>

    <Teleport to="body">
      <div v-if="showSwipeOverlay" class="swipe-overlay" @click.self="closeSwipeOverlay">
        <div class="overlay-header">
          <span class="index-text">{{ currentIndex + 1 }} / {{ articles.length }}</span>
          <button class="close-btn" @click="closeSwipeOverlay">×</button>
        </div>
        <div class="stack-wrap">
          <button class="nav-arrow nav-left" @click="prevSwipe" :disabled="currentIndex <= 0">‹</button>
          <button class="nav-arrow nav-right" @click="nextSwipe" :disabled="currentIndex >= articles.length - 1">›</button>
          <div v-for="(item, index) in articles.slice(currentIndex, currentIndex + 3)" :key="item.id" :class="['stack-card', `layer-${index}`, { swiping: index === 0 && swiping }]">
            <template v-if="index === 0">
              <h3>{{ item.title }}</h3>
              <p class="meta">{{ item.author }} · {{ item.created_at }}</p>
              <div class="content" v-html="item.content"></div>
              <div class="actions">
                <button class="action-btn" @click.stop="toggleLike(item)">{{ item.liked_by_me ? '取消赞' : '点赞' }} {{ item.likes_count }}</button>
                <button class="action-btn" @click.stop="loadComments(item.id)">评论 {{ item.comments_count }}</button>
              </div>
              <div class="comment-box">
                <AppInput v-model="commentInput[item.id]" placeholder="写下你的留言/评论" />
                <button class="action-btn" @click.stop="submitComment(item.id)">发布</button>
              </div>
              <div class="comments" v-if="commentsMap[item.id]?.length">
                <p v-for="comment in commentsMap[item.id]" :key="comment.id" class="comment-line">
                  <strong>{{ comment.username }}：</strong>{{ comment.content }}
                </p>
              </div>
            </template>
          </div>
        </div>
      </div>
    </Teleport>

    <AppDialog
      v-model="showDialog"
      title="提示"
      :message="dialogMessage"
      confirm-text="我知道了"
    />
  </div>
</template>

<style scoped>
.square-view { max-width: 980px; margin: 0 auto; padding: 32px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-hint { font-size: 13px; color: #555; }
.square-card { border: 1px solid #000; background: #fff; padding: 16px; margin-bottom: 16px; }
.meta { color: #555; font-size: 13px; margin: 8px 0; }
.content :deep(img) { max-width: 100%; border: 1px solid #000; }
.tags { margin: 10px 0; display: flex; gap: 8px; flex-wrap: wrap; }
.tag { border: 1px solid #000; padding: 2px 8px; font-size: 12px; }
.actions { display: flex; gap: 8px; margin-top: 8px; }
.action-btn { border: 1px solid #000; background: #fff; color: #000; padding: 6px 10px; cursor: pointer; }
.comment-box { display: flex; gap: 8px; margin-top: 12px; }
.comment-box :deep(.app-input) { flex: 1; }
.comments { margin-top: 10px; border-top: 1px solid #000; padding-top: 8px; }
.comment-line { margin: 6px 0; }
.error { color: #000; }

.swipe-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: rgba(0, 0, 0, 0.52);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  overscroll-behavior: contain;
}

.overlay-header {
  width: min(760px, 92vw);
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.index-text { color: #fff; }

.close-btn {
  border: 1px solid #000;
  background: #fff;
  color: #000;
  width: 34px;
  height: 34px;
  cursor: pointer;
  font-size: 22px;
  line-height: 28px;
}

.stack-wrap {
  position: relative;
  width: min(760px, 92vw);
  height: min(78vh, 760px);
}

.nav-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 42px;
  height: 42px;
  border: 1px solid #000;
  background: #fff;
  color: #000;
  font-size: 28px;
  line-height: 36px;
  cursor: pointer;
  z-index: 4;
}

.nav-left {
  left: -56px;
}

.nav-right {
  right: -56px;
}

.nav-arrow:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.stack-card {
  position: absolute;
  inset: 0;
  border: 1px solid #000;
  background: #fff;
  padding: 16px;
  overflow: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  transition: transform 220ms ease, opacity 220ms ease;
}

.stack-card.layer-1 {
  transform: translate(8px, 8px);
  z-index: 1;
}

.stack-card.layer-2 {
  transform: translate(16px, 16px);
  z-index: 0;
}

.stack-card.layer-0 {
  z-index: 2;
}

.stack-card.layer-0.swiping {
  transform: translateX(-120%);
  opacity: 0;
}
</style>
