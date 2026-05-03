<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { adminApi, type AlgorithmSettings, type ExperimentReport } from '@/api/admin'
import AppDialog from '@/components/AppDialog.vue'
import * as echarts from 'echarts'

const loading = ref(false)
const algorithm = ref<AlgorithmSettings | null>(null)
const showDialog = ref(false)
const dialogMessage = ref('')
const reportLoading = ref(false)
const report = ref<ExperimentReport | null>(null)
const chartEl = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const settingDocs = {
  decay_factor: {
    label: '衰减因子 decay_factor',
    formula: 'effective_weight = weight * (decay_factor ^ days)',
    range: '[0.50, 0.9999]（建议 0.90 ~ 0.98）',
    desc: '控制历史行为随时间衰减速度，越大越保留长期兴趣。'
  },
  similarity_weight: {
    label: '相似度权重 similarity_weight',
    formula: 'final = similarity * similarity_weight + ...',
    range: '[0, 1]（建议 0.40 ~ 0.70）',
    desc: '用户兴趣与文章标签匹配度在总分中的占比。'
  },
  hot_weight: {
    label: '热度权重 hot_weight',
    formula: 'final = hot_score * hot_weight + ...',
    range: '[0, 1]（建议 0.10 ~ 0.35）',
    desc: '文章热度（点赞+评论）在排序中的占比。'
  },
  follow_weight: {
    label: '关注权重 follow_weight',
    formula: 'final = follow_bonus * follow_weight + ...',
    range: '[0, 1]（建议 0.05 ~ 0.25）',
    desc: '对已关注作者内容的偏好加成权重。'
  },
  liked_weight: {
    label: '点赞偏好权重 liked_weight',
    formula: 'final = liked_bonus * liked_weight + ...',
    range: '[0, 1]（建议 0.01 ~ 0.10）',
    desc: '用户对已点赞内容的微弱偏好加权。'
  },
  diversity_penalty: {
    label: '多样性惩罚 diversity_penalty',
    formula: 'final = ... - diversity_penalty',
    range: '[0, 1]（建议 0.10 ~ 0.30）',
    desc: '连续出现同类标签内容时扣分，提升内容多样性。'
  },
  hot_like_factor: {
    label: '热度点赞系数 hot_like_factor',
    formula: 'hot_score = likes * hot_like_factor + comments * hot_comment_factor',
    range: '[0, 2]（建议 0.10 ~ 0.30）',
    desc: '每个点赞对热度分的贡献。'
  },
  hot_comment_factor: {
    label: '热度评论系数 hot_comment_factor',
    formula: 'hot_score = likes * hot_like_factor + comments * hot_comment_factor',
    range: '[0, 2]（建议 0.15 ~ 0.50）',
    desc: '每条评论对热度分的贡献，通常高于点赞系数。'
  },
  dwell_threshold_seconds: {
    label: '停留阈值 dwell_threshold_seconds',
    formula: 'dwell_seconds >= dwell_threshold_seconds 时记录停留',
    range: '[1, 600]（建议 10 ~ 30）',
    desc: '广场页面单篇文章在可视区域内停留达到该秒数后，计入停留统计并显示阅读时间。'
  },
  algo_mode: {
    label: '算法模式 algo_mode',
    formula: '0=full_model, 1=hot_only, 2=similarity_only, 3=sim_hot',
    range: '[0, 3]',
    desc: '用于快速切换完整模型与基线模型，支持对比实验。'
  }
} as const

const currentWeightSum = computed(() => {
  if (!algorithm.value) return 0
  return (
    algorithm.value.similarity_weight +
    algorithm.value.hot_weight +
    algorithm.value.follow_weight +
    algorithm.value.liked_weight
  )
})

const dwellThresholdHint = computed(() => {
  const value = algorithm.value?.dwell_threshold_seconds ?? 15
  if (value < 8) return '阈值较低，容易把快速浏览计入有效阅读。'
  if (value > 45) return '阈值较高，可能漏记正常阅读。'
  return '阈值区间合理，适合信息流场景。'
})

function tuneDwellThreshold(delta: number) {
  if (!algorithm.value) return
  const current = Number(algorithm.value.dwell_threshold_seconds || 15)
  const next = Math.max(1, Math.min(600, Math.round(current + delta)))
  algorithm.value.dwell_threshold_seconds = next
}

async function loadSettings() {
  loading.value = true
  try {
    algorithm.value = await adminApi.getAlgorithmSettings()
  } catch (error) {
    dialogMessage.value = '加载算法配置失败'
    showDialog.value = true
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  if (!algorithm.value) return
  try {
    await adminApi.updateAlgorithmSettings(algorithm.value)
    algorithm.value = await adminApi.getAlgorithmSettings()
    dialogMessage.value = '算法配置已保存'
    showDialog.value = true
  } catch (error: any) {
    dialogMessage.value = error?.response?.data?.detail || '保存失败'
    showDialog.value = true
  }
}

async function resetSettings() {
  try {
    algorithm.value = await adminApi.resetAlgorithmSettings()
    dialogMessage.value = '已恢复默认值'
    showDialog.value = true
  } catch (error) {
    dialogMessage.value = '恢复默认值失败'
    showDialog.value = true
  }
}

async function generateReport() {
  reportLoading.value = true
  try {
    report.value = await adminApi.generateExperimentReport()
    await nextTick()
    renderChart()
    dialogMessage.value = '实验报告生成成功'
    showDialog.value = true
  } catch (error: any) {
    dialogMessage.value = error?.response?.data?.detail || '实验报告生成失败'
    showDialog.value = true
  } finally {
    reportLoading.value = false
  }
}

function renderChart() {
  if (!report.value || !chartEl.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartEl.value)
  }

  const categories = report.value.summaries.map((item) => `mode ${item.mode}`)
  const recallValues = report.value.summaries.map((item) => item.recall_at_10)
  const ndcgValues = report.value.summaries.map((item) => item.ndcg_at_10)

  chartInstance.setOption({
    title: { text: '实时实验对比图（Recall@10 / NDCG@10）', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['Recall@10', 'NDCG@10'], top: 30 },
    grid: { left: 40, right: 30, top: 70, bottom: 30, containLabel: true },
    xAxis: { type: 'category', data: categories },
    yAxis: { type: 'value', min: 0, max: 1 },
    series: [
      { name: 'Recall@10', type: 'bar', data: recallValues, itemStyle: { color: '#000000' } },
      { name: 'NDCG@10', type: 'bar', data: ndcgValues, itemStyle: { color: '#9a9a9a' } }
    ]
  })
}

async function downloadReport(kind: 'csv' | 'md' | 'png') {
  if (!report.value) return
  const target = kind === 'csv' ? report.value.csv_url : kind === 'md' ? report.value.md_url : report.value.png_url
  const blob = await adminApi.fetchReportFile(target)
  const url = URL.createObjectURL(blob)
  const name = target.split('/').pop() || `report.${kind}`
  const link = document.createElement('a')
  link.href = url
  link.download = name
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadSettings()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<template>
  <div class="topology-view">
    <h1>算法配置（管理员）</h1>
    <div v-if="loading">加载中...</div>
    <section v-else-if="algorithm" class="panel users">
      <p class="rule-line">权重约束：similarity_weight + hot_weight + follow_weight + liked_weight = 1</p>
      <p class="rule-line">
        当前总权重：
        <strong :style="{ color: Math.abs(currentWeightSum - 1) < 0.000001 ? '#000' : '#b00020' }">
          {{ currentWeightSum.toFixed(6) }}
        </strong>
      </p>
      <div class="algo-grid">
        <div class="algo-item">
          <label>{{ settingDocs.decay_factor.label }} <input v-model.number="algorithm.decay_factor" type="number" step="0.01" /></label>
          <p>说明：{{ settingDocs.decay_factor.desc }}</p>
          <p>公式：{{ settingDocs.decay_factor.formula }}</p>
          <p>建议范围：{{ settingDocs.decay_factor.range }}</p>
        </div>
        <div class="algo-item">
          <label>{{ settingDocs.similarity_weight.label }} <input v-model.number="algorithm.similarity_weight" type="number" step="0.01" /></label>
          <p>说明：{{ settingDocs.similarity_weight.desc }}</p>
          <p>公式：{{ settingDocs.similarity_weight.formula }}</p>
          <p>建议范围：{{ settingDocs.similarity_weight.range }}</p>
        </div>
        <div class="algo-item">
          <label>{{ settingDocs.hot_weight.label }} <input v-model.number="algorithm.hot_weight" type="number" step="0.01" /></label>
          <p>说明：{{ settingDocs.hot_weight.desc }}</p>
          <p>公式：{{ settingDocs.hot_weight.formula }}</p>
          <p>建议范围：{{ settingDocs.hot_weight.range }}</p>
        </div>
        <div class="algo-item">
          <label>{{ settingDocs.follow_weight.label }} <input v-model.number="algorithm.follow_weight" type="number" step="0.01" /></label>
          <p>说明：{{ settingDocs.follow_weight.desc }}</p>
          <p>公式：{{ settingDocs.follow_weight.formula }}</p>
          <p>建议范围：{{ settingDocs.follow_weight.range }}</p>
        </div>
        <div class="algo-item">
          <label>{{ settingDocs.liked_weight.label }} <input v-model.number="algorithm.liked_weight" type="number" step="0.01" /></label>
          <p>说明：{{ settingDocs.liked_weight.desc }}</p>
          <p>公式：{{ settingDocs.liked_weight.formula }}</p>
          <p>建议范围：{{ settingDocs.liked_weight.range }}</p>
        </div>
        <div class="algo-item">
          <label>{{ settingDocs.diversity_penalty.label }} <input v-model.number="algorithm.diversity_penalty" type="number" step="0.01" /></label>
          <p>说明：{{ settingDocs.diversity_penalty.desc }}</p>
          <p>公式：{{ settingDocs.diversity_penalty.formula }}</p>
          <p>建议范围：{{ settingDocs.diversity_penalty.range }}</p>
        </div>
        <div class="algo-item">
          <label>{{ settingDocs.hot_like_factor.label }} <input v-model.number="algorithm.hot_like_factor" type="number" step="0.01" /></label>
          <p>说明：{{ settingDocs.hot_like_factor.desc }}</p>
          <p>公式：{{ settingDocs.hot_like_factor.formula }}</p>
          <p>建议范围：{{ settingDocs.hot_like_factor.range }}</p>
        </div>
        <div class="algo-item">
          <label>{{ settingDocs.hot_comment_factor.label }} <input v-model.number="algorithm.hot_comment_factor" type="number" step="0.01" /></label>
          <p>说明：{{ settingDocs.hot_comment_factor.desc }}</p>
          <p>公式：{{ settingDocs.hot_comment_factor.formula }}</p>
          <p>建议范围：{{ settingDocs.hot_comment_factor.range }}</p>
        </div>
        <div class="algo-item">
          <label>{{ settingDocs.dwell_threshold_seconds.label }} <input v-model.number="algorithm.dwell_threshold_seconds" type="number" step="1" min="1" max="600" /></label>
          <p>说明：{{ settingDocs.dwell_threshold_seconds.desc }}</p>
          <p>公式：{{ settingDocs.dwell_threshold_seconds.formula }}</p>
          <p>建议范围：{{ settingDocs.dwell_threshold_seconds.range }}</p>
          <div class="threshold-tools">
            <button class="btn mini" type="button" @click="tuneDwellThreshold(-5)">-5s</button>
            <button class="btn mini" type="button" @click="tuneDwellThreshold(5)">+5s</button>
            <span>当前值：{{ Math.round(algorithm.dwell_threshold_seconds) }} 秒</span>
          </div>
          <p class="threshold-hint">{{ dwellThresholdHint }}</p>
        </div>
        <div class="algo-item">
          <label>{{ settingDocs.algo_mode.label }} <input v-model.number="algorithm.algo_mode" type="number" step="1" min="0" max="3" /></label>
          <p>说明：{{ settingDocs.algo_mode.desc }}</p>
          <p>公式：{{ settingDocs.algo_mode.formula }}</p>
          <p>建议范围：{{ settingDocs.algo_mode.range }}</p>
        </div>
      </div>
      <div style="display:flex; gap:8px;">
        <button class="btn" @click="saveSettings">保存算法变量</button>
        <button class="btn" @click="resetSettings">恢复默认值</button>
        <button class="btn" :disabled="reportLoading" @click="generateReport">
          {{ reportLoading ? '生成中...' : '生成实验报告' }}
        </button>
      </div>

      <div v-if="report" class="report-panel">
        <h3>实时实验数据</h3>
        <p>生成时间：{{ report.generated_at }}</p>
        <table class="report-table">
          <thead>
            <tr>
              <th>mode（模型编号）</th>
              <th>模型名称</th>
              <th>users（参与评估用户数）</th>
              <th>recall@10（前10条命中率）</th>
              <th>ndcg@10（前10条排序质量）</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in report.summaries" :key="row.mode">
              <td>{{ row.mode }}</td>
              <td>{{ row.mode_name }}</td>
              <td>{{ row.users }}</td>
              <td>{{ row.recall_at_10 }}</td>
              <td>{{ row.ndcg_at_10 }}</td>
            </tr>
          </tbody>
        </table>
        <div class="report-notes">
          <p><strong>术语说明：</strong></p>
          <p>mode/模型名称对应：0=full_model，1=hot_only，2=similarity_only，3=sim_hot。</p>
          <p>users：本次离线评估中纳入统计的用户数量（行为样本不足的用户不会计入）。</p>
          <p>recall@10：真实目标内容是否出现在前10条推荐中的比例，越高表示“能推中”。</p>
          <p>ndcg@10：考虑命中位置的排序质量指标，越高表示“推得准且排得靠前”。</p>
        </div>
        <div class="downloads">
          <button class="btn" @click="downloadReport('csv')">下载 CSV</button>
          <button class="btn" @click="downloadReport('md')">下载 MD</button>
          <button class="btn" @click="downloadReport('png')">下载 PNG</button>
        </div>
        <div ref="chartEl" class="chart"></div>
      </div>
    </section>

    <AppDialog v-model="showDialog" title="提示" :message="dialogMessage" confirm-text="我知道了" />
  </div>
</template>

<style scoped>
.topology-view { max-width: 1000px; margin: 0 auto; padding: 32px; }
.panel { border: 1px solid #000; background: #fff; padding: 14px; }
.users { grid-column: 1 / -1; }
.btn { border: 1px solid #000; background: #fff; color: #000; padding: 4px 10px; cursor: pointer; }
.btn.mini { padding: 2px 8px; font-size: 12px; }
.algo-grid { display: grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 8px; margin: 10px 0; }
.algo-item { border: 1px solid #000; padding: 8px; }
.algo-grid label { display: flex; justify-content: space-between; gap: 8px; align-items: center; font-weight: 700; }
.algo-item p { margin-top: 6px; font-size: 13px; line-height: 1.4; }
.algo-grid input { border: 1px solid #000; padding: 4px 6px; width: 110px; }
.rule-line { margin-bottom: 8px; font-size: 13px; }
.report-panel { margin-top: 14px; border-top: 1px solid #000; padding-top: 12px; }
.report-table { width: 100%; border-collapse: collapse; margin-top: 8px; }
.report-table th, .report-table td { border: 1px solid #000; padding: 6px 8px; font-size: 13px; text-align: left; }
.report-notes { border: 1px solid #000; border-top: none; padding: 8px 10px; font-size: 13px; }
.report-notes p { margin: 4px 0; }
.downloads { display: flex; gap: 12px; margin: 10px 0; }
.downloads a { color: #000; text-decoration: underline; }
.chart { width: 100%; max-width: 760px; height: 380px; border: 1px solid #000; }
.threshold-tools { display: flex; align-items: center; gap: 8px; margin-top: 8px; font-size: 12px; }
.threshold-hint { margin-top: 6px; font-size: 12px; color: #333; }
</style>
