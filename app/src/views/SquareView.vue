<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { articlesApi } from '@/api/articles'
import { adminApi, type AlgorithmCurrent } from '@/api/admin'
import type { SquareArticle, ArticleComment } from '@/types/article'
import AppInput from '@/components/AppInput.vue'
import AppDialog from '@/components/AppDialog.vue'
import EmptyWiltedFlower from '@/components/EmptyWiltedFlower.vue'

const loading = ref(false)
const error = ref('')
const articles = ref<SquareArticle[]>([])
const commentsMap = ref<Record<string, ArticleComment[]>>({})
const commentInput = ref<Record<string, string>>({})
const showDialog = ref(false)
const dialogMessage = ref('')
const sortBy = ref<'recommend' | 'latest'>('recommend')
const algorithmCurrent = ref<AlgorithmCurrent | null>(null)
const dwellDisplaySeconds = ref<Record<string, number>>({})
const dwellQualified = ref<Record<string, boolean>>({})
const dwellFinalSeconds = ref<Record<string, number>>({})

const articleElements = new Map<string, HTMLElement>()
const visibleSince = new Map<string, number>()
const accumulatedMs = new Map<string, number>()
const dwellTimers = new Map<string, number>()
const dwellIntervals = new Map<string, number>()
const reportedInSession = new Set<string>()
let articleObserver: IntersectionObserver | null = null

const dwellThresholdSeconds = computed(() => {
  const value = Number(algorithmCurrent.value?.dwell_threshold_seconds ?? 15)
  if (!Number.isFinite(value)) return 15
  return Math.max(1, Math.round(value))
})

const sortedArticles = computed(() => {
  const list = [...articles.value]
  if (sortBy.value === 'recommend') {
    return list.sort((a, b) => (b.recommend_score || 0) - (a.recommend_score || 0))
  }
  return list.sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
})

async function loadSquare() {
  loading.value = true
  error.value = ''
  try {
    articles.value = await articlesApi.square()
    await Promise.all(articles.value.map((item) => loadComments(item.id)))
    algorithmCurrent.value = await adminApi.getAlgorithmCurrent()
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

async function reportDwellIfNeeded(articleId: string) {
  if (reportedInSession.has(articleId)) return
  const dwellSeconds = getCurrentDwellSeconds(articleId)
  if (dwellSeconds < dwellThresholdSeconds.value) return

  try {
    await articlesApi.reportDwell(articleId, dwellSeconds)
    reportedInSession.add(articleId)
  } catch (error) {
  }
}

function getCurrentDwellMs(articleId: string) {
  const base = accumulatedMs.get(articleId) || 0
  const start = visibleSince.get(articleId)
  if (!start) return base
  return base + Math.max(0, Date.now() - start)
}

function getCurrentDwellSeconds(articleId: string) {
  return Math.max(1, Math.round(getCurrentDwellMs(articleId) / 1000))
}

function setDwellQualified(articleId: string, value: boolean) {
  dwellQualified.value = {
    ...dwellQualified.value,
    [articleId]: value
  }
}

function setDwellFinalSeconds(articleId: string, seconds: number) {
  dwellFinalSeconds.value = {
    ...dwellFinalSeconds.value,
    [articleId]: seconds
  }
}

function clearDwellFinalSeconds(articleId: string) {
  if (!(articleId in dwellFinalSeconds.value)) return
  dwellFinalSeconds.value = Object.fromEntries(
    Object.entries(dwellFinalSeconds.value).filter(([key]) => key !== articleId)
  )
}

function clearDwellQualified(articleId: string) {
  if (!(articleId in dwellQualified.value)) return
  dwellQualified.value = Object.fromEntries(
    Object.entries(dwellQualified.value).filter(([key]) => key !== articleId)
  )
}

function setDwellDisplay(articleId: string, seconds: number) {
  dwellDisplaySeconds.value = {
    ...dwellDisplaySeconds.value,
    [articleId]: seconds
  }
}

function clearDwellDisplay(articleId: string) {
  if (!(articleId in dwellDisplaySeconds.value)) return
  dwellDisplaySeconds.value = Object.fromEntries(
    Object.entries(dwellDisplaySeconds.value).filter(([key]) => key !== articleId)
  )
}

function finalizeVisibleSpan(articleId: string) {
  const start = visibleSince.get(articleId)
  if (!start) return
  const prev = accumulatedMs.get(articleId) || 0
  accumulatedMs.set(articleId, prev + Math.max(0, Date.now() - start))
  visibleSince.delete(articleId)
}

function clearDwellInterval(articleId: string) {
  const timer = dwellIntervals.get(articleId)
  if (timer !== undefined) {
    window.clearInterval(timer)
    dwellIntervals.delete(articleId)
  }
}

function startDwellDisplay(articleId: string) {
  clearDwellInterval(articleId)
  setDwellDisplay(articleId, getCurrentDwellSeconds(articleId))
  setDwellQualified(articleId, true)
  clearDwellFinalSeconds(articleId)

  const timer = window.setInterval(() => {
    if (!visibleSince.has(articleId)) {
      clearDwellInterval(articleId)
      return
    }
    setDwellDisplay(articleId, getCurrentDwellSeconds(articleId))
  }, 1000)
  dwellIntervals.set(articleId, timer)
}

function clearDwellTimer(articleId: string) {
  const timer = dwellTimers.get(articleId)
  if (timer !== undefined) {
    window.clearTimeout(timer)
    dwellTimers.delete(articleId)
  }
}

function scheduleDwellTimer(articleId: string) {
  clearDwellTimer(articleId)
  if (reportedInSession.has(articleId)) return

  const remainingMs = Math.max(0, dwellThresholdSeconds.value * 1000 - getCurrentDwellMs(articleId))
  if (remainingMs <= 0) {
    startDwellDisplay(articleId)
    reportDwellIfNeeded(articleId)
    return
  }

  const timer = window.setTimeout(async () => {
    startDwellDisplay(articleId)
    await reportDwellIfNeeded(articleId)
    clearDwellTimer(articleId)
  }, remainingMs)
  dwellTimers.set(articleId, timer)
}

function handleArticleVisibility(articleId: string, isVisible: boolean) {
  if (isVisible) {
    if (!visibleSince.has(articleId)) {
      visibleSince.set(articleId, Date.now())
      scheduleDwellTimer(articleId)
      if (dwellQualified.value[articleId]) {
        startDwellDisplay(articleId)
      }
    }
    return
  }

  finalizeVisibleSpan(articleId)
  reportDwellIfNeeded(articleId)
  if (dwellQualified.value[articleId]) {
    const finalSeconds = getCurrentDwellSeconds(articleId)
    setDwellFinalSeconds(articleId, finalSeconds)
  }
  clearDwellTimer(articleId)
  clearDwellInterval(articleId)
  clearDwellDisplay(articleId)
}

function setupObserver() {
  if (articleObserver) {
    articleObserver.disconnect()
  }

  articleObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        const element = entry.target as HTMLElement
        const articleId = element.dataset.articleId
        if (!articleId) return
        const ratio = entry.intersectionRatio || 0
        handleArticleVisibility(articleId, entry.isIntersecting && ratio >= 0.6)
      })
    },
    {
      threshold: [0, 0.4, 0.6, 0.8, 1]
    }
  )

  articleElements.forEach(el => {
    articleObserver?.observe(el)
  })
}

function bindArticleRef(el: Element | null, articleId: string) {
  if (el) {
    articleElements.set(articleId, el as HTMLElement)
    if (articleObserver) {
      articleObserver.observe(el)
    }
    return
  }

  const existing = articleElements.get(articleId)
  if (existing && articleObserver) {
    articleObserver.unobserve(existing)
  }
  articleElements.delete(articleId)
  finalizeVisibleSpan(articleId)
  clearDwellTimer(articleId)
  clearDwellInterval(articleId)
  clearDwellDisplay(articleId)
  clearDwellQualified(articleId)
  clearDwellFinalSeconds(articleId)
  accumulatedMs.delete(articleId)
}

onMounted(() => {
  loadSquare()
})

watch(
  () => sortedArticles.value.map(item => item.id).join(','),
  async () => {
    await nextTick()
    setupObserver()
  }
)

watch(dwellThresholdSeconds, () => {
  visibleSince.forEach((_, articleId) => {
    clearDwellTimer(articleId)
    clearDwellInterval(articleId)
    clearDwellDisplay(articleId)
    clearDwellQualified(articleId)
    clearDwellFinalSeconds(articleId)
    reportedInSession.delete(articleId)
    if (!reportedInSession.has(articleId)) {
      scheduleDwellTimer(articleId)
    }
  })
})

onBeforeUnmount(() => {
  visibleSince.forEach((_, articleId) => {
    finalizeVisibleSpan(articleId)
    reportDwellIfNeeded(articleId)
  })

  dwellTimers.forEach(timer => {
    window.clearTimeout(timer)
  })
  dwellIntervals.forEach(timer => {
    window.clearInterval(timer)
  })
  dwellTimers.clear()
  dwellIntervals.clear()
  visibleSince.clear()
  accumulatedMs.clear()
  dwellDisplaySeconds.value = {}
  dwellQualified.value = {}
  dwellFinalSeconds.value = {}

  if (articleObserver) {
    articleObserver.disconnect()
    articleObserver = null
  }
})
</script>

<template>
  <div class="square-view">
    <div class="header">
      <h1>广场</h1>
      <p class="header-hint">个性化推荐信息流</p>
    </div>

    <div class="sort-bar">
      <span class="sort-label">排序：</span>
      <button
        class="action-btn"
        :class="{ active: sortBy === 'recommend' }"
        @click="sortBy = 'recommend'"
      >
        推荐分
      </button>
      <button
        class="action-btn"
        :class="{ active: sortBy === 'latest' }"
        @click="sortBy = 'latest'"
      >
        最新发布时间
      </button>
    </div>

    <div v-if="algorithmCurrent" class="algo-panel">
      <p><strong>当前模型：</strong>{{ algorithmCurrent.mode_name }} (mode {{ algorithmCurrent.algo_mode }})</p>
      <p>
        <strong>当前权重：</strong>
        similarity={{ algorithmCurrent.similarity_weight }}，
        hot={{ algorithmCurrent.hot_weight }}，
        follow={{ algorithmCurrent.follow_weight }}，
        liked={{ algorithmCurrent.liked_weight }}，
        diversity_penalty={{ algorithmCurrent.diversity_penalty }}
      </p>
      <p>
        <strong>热度系数：</strong>
        like_factor={{ algorithmCurrent.hot_like_factor }}，
        comment_factor={{ algorithmCurrent.hot_comment_factor }}，
        decay={{ algorithmCurrent.decay_factor }}
      </p>
      <p><strong>停留阈值：</strong>{{ dwellThresholdSeconds }} 秒</p>
    </div>

    <div v-if="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <EmptyWiltedFlower v-else-if="articles.length === 0" text="广场暂无内容" />

    <div v-else class="feed-list">
      <article
        v-for="item in sortedArticles"
        :key="item.id"
        :ref="el => bindArticleRef(el as Element | null, item.id)"
        class="square-card"
        :data-article-id="item.id"
      >
        <div v-if="dwellDisplaySeconds[item.id]" class="dwell-badge is-live">
          阅读时间 {{ dwellDisplaySeconds[item.id] }}s
        </div>
        <div v-else-if="dwellFinalSeconds[item.id]" class="dwell-badge is-final">
          本次阅读 {{ dwellFinalSeconds[item.id] }}s
        </div>
        <h3>{{ item.title }}</h3>
        <p class="meta">{{ item.author }} · {{ item.created_at }}</p>
        <div class="content" v-html="item.content"></div>
        <div class="tags">
          <span v-for="tag in item.tags" :key="tag.id" class="tag">{{ tag.name }}</span>
        </div>
        <div class="actions">
          <button class="action-btn" @click.stop="toggleLike(item)">{{ item.liked_by_me ? '取消赞' : '点赞' }} {{ item.likes_count }}</button>
          <span class="comment-count">评论 {{ item.comments_count }}</span>
        </div>
        <div class="recommend-tip" v-if="item.recommend_reason">
          <p class="tip-title">{{ item.recommend_reason.tip }}：</p>
          <p class="tip-line">推荐分：{{ item.recommend_score.toFixed(4) }}</p>
          <p class="tip-line">命中标签：{{ item.recommend_reason.matched_tags.join('、') }}</p>
          <p class="tip-line">算法结果：0.6×相似度({{ item.recommend_reason.similarity_score.toFixed(3) }}) + 0.2×热度({{ item.recommend_reason.hot_score.toFixed(3) }}) + 0.15×关注加成({{ item.recommend_reason.follow_bonus.toFixed(1) }}) + 0.05×点赞偏好({{ item.recommend_reason.liked_bonus.toFixed(1) }}) - 多样性惩罚({{ item.recommend_reason.diversity_penalty.toFixed(1) }})</p>
        </div>
        <div class="comment-box" @click.stop>
          <AppInput v-model="commentInput[item.id]" placeholder="写下你的留言/评论" />
          <button class="action-btn" @click.stop="submitComment(item.id)">发布</button>
        </div>
        <div class="comments" @click.stop>
          <p v-if="!commentsMap[item.id] || commentsMap[item.id].length === 0" class="comment-line">暂无评论</p>
          <p v-for="comment in commentsMap[item.id]" :key="comment.id" class="comment-line">
            <strong>{{ comment.username }}：</strong>{{ comment.content }}
          </p>
        </div>
      </article>
    </div>

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
.sort-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.sort-label { font-size: 13px; color: #555; }
.algo-panel { border: 1px solid #000; background: #fff; padding: 10px; margin-bottom: 12px; font-size: 13px; }
.algo-panel p { margin: 4px 0; }
.square-card { position: relative; border: 1px solid #000; background: #fff; padding: 16px; margin-bottom: 16px; }
.square-card::before { content: ''; position: absolute; left: -1px; top: -1px; width: 12px; height: 12px; border-top: 2px solid #000; border-left: 2px solid #000; }
.square-card::after { content: ''; position: absolute; right: -1px; bottom: -1px; width: 12px; height: 12px; border-right: 2px solid #000; border-bottom: 2px solid #000; }
.dwell-badge { position: absolute; top: -1px; right: -1px; border: 1px solid #000; padding: 4px 10px; font-size: 12px; }
.dwell-badge.is-live { background: #000; color: #fff; }
.dwell-badge.is-final { background: #fff; color: #000; }
.meta { color: #555; font-size: 13px; margin: 8px 0; }
.content :deep(img) { max-width: 100%; border: 1px solid #000; }
.tags { margin: 10px 0; display: flex; gap: 8px; flex-wrap: wrap; }
.tag { border: 1px solid #000; padding: 2px 8px; font-size: 12px; }
.actions { display: flex; gap: 8px; margin-top: 8px; }
.action-btn { border: 1px solid #000; background: #fff; color: #000; padding: 6px 10px; cursor: pointer; }
.comment-count { border: 1px solid #000; padding: 6px 10px; font-size: 13px; }
.action-btn.active { background: #000; color: #fff; }
.recommend-tip { margin-top: 10px; border-left: 3px solid #000; padding-left: 10px; }
.tip-title { margin: 0 0 4px; font-weight: 700; }
.tip-line { margin: 3px 0; font-size: 13px; color: #222; }
.comment-box { display: flex; gap: 8px; margin-top: 12px; }
.comment-box :deep(.app-input) { flex: 1; }
.comments { margin-top: 10px; border-top: 1px solid #000; padding-top: 8px; }
.comment-line { margin: 6px 0; }
.error { color: #000; }
</style>
