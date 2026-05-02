<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { topologyApi } from '@/api/topology'
import { socialApi, type SocialUser } from '@/api/social'
import { adminApi, type AlgorithmSettings } from '@/api/admin'
import AppDialog from '@/components/AppDialog.vue'
import * as echarts from 'echarts'

const loading = ref(false)
const overview = ref<any>(null)
const graph = ref<any>(null)
const users = ref<SocialUser[]>([])
const algorithm = ref<AlgorithmSettings | null>(null)
const showDialog = ref(false)
const dialogMessage = ref('')
const graphEl = ref<HTMLElement | null>(null)
let graphChart: echarts.ECharts | null = null
let renderRetryTimer: number | null = null

const userNodeCount = ref(0)
const tagNodeCount = ref(0)
const graphStatus = ref('未渲染')

async function loadData() {
  loading.value = true
  try {
    const [ov, gr, us] = await Promise.all([
      topologyApi.overview(),
      topologyApi.graph(),
      socialApi.users()
    ])
    overview.value = ov
    graph.value = gr
    userNodeCount.value = (gr?.nodes || []).filter((n: any) => n.node_type === 'user').length
    tagNodeCount.value = (gr?.nodes || []).filter((n: any) => n.node_type === 'tag').length
    users.value = us
    algorithm.value = await adminApi.getAlgorithmSettings()
    await nextTick()
    renderGraph()
  } catch (error) {
    dialogMessage.value = '拓扑数据加载失败'
    showDialog.value = true
  } finally {
    loading.value = false
  }
}

function renderGraph() {
  if (!graph.value) {
    graphStatus.value = '无图数据'
    return
  }
  if (!graphEl.value) {
    graphStatus.value = '等待容器挂载'
    return
  }

  try {
    graphStatus.value = '渲染中'
    if (!graphChart) {
      graphChart = echarts.init(graphEl.value, undefined, { renderer: 'svg' })
    }

  const nodes = (graph.value.nodes || []).map((n: any) => ({
    id: n.id,
    name: n.name,
    value: n.node_type,
    category: n.node_type === 'user' ? 0 : 1,
    symbol: n.node_type === 'user' && n.avatar_url ? `image://${n.avatar_url}` : 'circle',
    symbolSize: n.node_type === 'user' ? 36 : 16,
    itemStyle: {
      color: n.node_type === 'user' ? '#000000' : '#ffffff',
      borderColor: '#000000',
      borderWidth: 1
    },
    label: {
      show: true,
      color: '#000000',
      fontSize: 9,
      position: 'bottom',
      distance: 4,
      formatter: (params: any) => params.data.name
    }
  }))

  const links = (graph.value.edges || []).slice(0, 240).map((e: any) => ({
    source: e.source,
    target: e.target,
    value: e.weight,
    lineStyle: {
      color: '#666666',
      width: Math.max(1, Math.min(4, Number(e.weight || 1)))
    }
  }))

    graphChart.setOption({
    tooltip: {
      backgroundColor: '#ffffff',
      borderColor: '#000000',
      borderWidth: 1,
      textStyle: {
        color: '#000000'
      },
      formatter: (params: any) => {
        if (params.dataType === 'edge') {
          return `关系强度: ${params.data.value}`
        }
        return `${params.data.name} (${params.data.value})`
      }
    },
    legend: {
      top: 30,
      textStyle: {
        color: '#000000'
      },
      data: ['用户节点', '标签节点']
    },
    series: [
      {
        type: 'graph',
        layout: 'circular',
        animation: false,
        roam: true,
        draggable: true,
        edgeSymbol: ['none', 'none'],
        edgeSymbolSize: 6,
        circular: {
          rotateLabel: false
        },
        categories: [
          { name: '用户节点', itemStyle: { color: '#000000' } },
          { name: '标签节点', itemStyle: { color: '#9a9a9a' } }
        ],
        data: nodes,
        links,
        lineStyle: {
          opacity: 0.55,
          curveness: 0.2
        },
        emphasis: {
          focus: 'adjacency'
        }
      }
    ]
    }, { notMerge: true, lazyUpdate: false })

    window.setTimeout(() => {
      graphChart?.resize()
    }, 120)
    graphStatus.value = `已渲染：nodes=${nodes.length}, edges=${links.length}`
  } catch (error) {
    graphStatus.value = '渲染失败'
    dialogMessage.value = '拓扑图渲染失败，请刷新重试'
    showDialog.value = true
  }
}

function scheduleRenderRetry() {
  if (renderRetryTimer !== null) {
    window.clearInterval(renderRetryTimer)
    renderRetryTimer = null
  }
  let attempts = 0
  renderRetryTimer = window.setInterval(() => {
    attempts += 1
    if (graphEl.value && graph.value) {
      renderGraph()
      window.clearInterval(renderRetryTimer as number)
      renderRetryTimer = null
      return
    }
    if (attempts >= 20) {
      graphStatus.value = '容器未就绪（重试超时）'
      window.clearInterval(renderRetryTimer as number)
      renderRetryTimer = null
    }
  }, 120)
}

watch([graphEl, graph], async () => {
  await nextTick()
  renderGraph()
  scheduleRenderRetry()
})

async function saveAlgorithm() {
  if (!algorithm.value) return
  try {
    algorithm.value = await adminApi.updateAlgorithmSettings(algorithm.value)
    dialogMessage.value = '算法变量已更新'
    showDialog.value = true
  } catch (error) {
    dialogMessage.value = '算法变量更新失败'
    showDialog.value = true
  }
}

async function resetAlgorithm() {
  try {
    algorithm.value = await adminApi.resetAlgorithmSettings()
    dialogMessage.value = '已恢复默认算法变量'
    showDialog.value = true
  } catch (error) {
    dialogMessage.value = '恢复默认值失败'
    showDialog.value = true
  }
}

async function toggleFollow(userId: string) {
  await socialApi.toggleFollow(userId)
  await loadData()
}

onMounted(() => {
  loadData()
})

onBeforeUnmount(() => {
  if (graphChart) {
    graphChart.dispose()
    graphChart = null
  }
  if (renderRetryTimer !== null) {
    window.clearInterval(renderRetryTimer)
    renderRetryTimer = null
  }
})
</script>

<template>
  <div class="topology-view">
    <h1>拓扑分析</h1>
    <div v-if="loading">加载中...</div>
    <div v-else-if="overview" class="grid">
      <section class="panel metrics metrics-panel">
        <h3>算法指标</h3>
        <p>用户总数：{{ overview.users_count }}</p>
        <p>关注关系：{{ overview.follows_count }}</p>
        <p>点赞总量：{{ overview.likes_count }}</p>
        <p>评论总量：{{ overview.comments_count }}</p>
        <p>我的关注：{{ overview.my_following }}</p>
        <p>我的粉丝：{{ overview.my_followers }}</p>
        <p>关注分数：{{ overview.my_attention_score }}</p>
      </section>

      <section class="panel graph-panel">
        <h3>用户-标签关系图概览</h3>
        <p>节点数：{{ graph?.nodes?.length || 0 }}</p>
        <p>边数：{{ graph?.edges?.length || 0 }}</p>
        <p>用户节点：{{ userNodeCount }}</p>
        <p>标签节点：{{ tagNodeCount }}</p>
        <p>图状态：{{ graphStatus }}</p>
        <div ref="graphEl" class="echart-graph"></div>
        <div class="edge-list">
          <p v-for="e in (graph?.edges || []).slice(0, 12)" :key="`${e.source}-${e.target}`">
            {{ e.source }} → {{ e.target }} ｜关系：{{ e.relation }} ｜强度：{{ e.weight }} ｜次数：{{ e.count }}
          </p>
        </div>
      </section>
    </div>

    <AppDialog v-model="showDialog" title="提示" :message="dialogMessage" confirm-text="我知道了" />
  </div>
</template>

<style scoped>
.topology-view { max-width: 1280px; margin: 0 auto; padding: 32px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.panel { border: 1px solid #000; background: #fff; padding: 14px; }
.metrics-panel { grid-column: 1 / -1; }
.graph-panel { grid-column: 1 / -1; }
.metrics p { margin: 6px 0; }
.echart-graph { margin-top: 10px; width: 100%; height: 760px; border: 1px solid #000; }
.edge-list { margin-top: 10px; border-top: 1px solid #000; padding-top: 8px; font-size: 12px; }
.edge-list p { margin: 4px 0; }
</style>
