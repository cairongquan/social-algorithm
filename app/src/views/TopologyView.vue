<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { topologyApi } from '@/api/topology'
import { socialApi, type SocialUser } from '@/api/social'
import AppDialog from '@/components/AppDialog.vue'

const loading = ref(false)
const overview = ref<any>(null)
const graph = ref<any>(null)
const users = ref<SocialUser[]>([])
const showDialog = ref(false)
const dialogMessage = ref('')

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
    users.value = us
  } catch (error) {
    dialogMessage.value = '拓扑数据加载失败'
    showDialog.value = true
  } finally {
    loading.value = false
  }
}

async function toggleFollow(userId: string) {
  await socialApi.toggleFollow(userId)
  await loadData()
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="topology-view">
    <h1>拓扑分析</h1>
    <div v-if="loading">加载中...</div>
    <div v-else-if="overview" class="grid">
      <section class="panel metrics">
        <h3>算法指标</h3>
        <p>用户总数：{{ overview.users_count }}</p>
        <p>关注关系：{{ overview.follows_count }}</p>
        <p>点赞总量：{{ overview.likes_count }}</p>
        <p>评论总量：{{ overview.comments_count }}</p>
        <p>我的关注：{{ overview.my_following }}</p>
        <p>我的粉丝：{{ overview.my_followers }}</p>
        <p>关注分数：{{ overview.my_attention_score }}</p>
      </section>

      <section class="panel">
        <h3>关注图概览</h3>
        <p>节点数：{{ graph?.nodes?.length || 0 }}</p>
        <p>边数：{{ graph?.edges?.length || 0 }}</p>
        <div class="mini-graph">
          <div v-for="n in (graph?.nodes || []).slice(0, 24)" :key="n.id" class="node">{{ n.username[0] }}</div>
        </div>
      </section>

      <section class="panel users">
        <h3>用户关注管理</h3>
        <div v-for="u in users" :key="u.id" class="user-row">
          <div class="name">{{ u.username }}</div>
          <button class="btn" @click="toggleFollow(u.id)">{{ u.followed_by_me ? '取消关注' : '关注' }}</button>
        </div>
      </section>
    </div>

    <AppDialog v-model="showDialog" title="提示" :message="dialogMessage" confirm-text="我知道了" />
  </div>
</template>

<style scoped>
.topology-view { max-width: 1000px; margin: 0 auto; padding: 32px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.panel { border: 1px solid #000; background: #fff; padding: 14px; }
.metrics p { margin: 6px 0; }
.mini-graph { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.node { width: 30px; height: 30px; border: 1px solid #000; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; }
.users { grid-column: 1 / -1; }
.user-row { display: flex; justify-content: space-between; border-top: 1px solid #000; padding: 8px 0; }
.btn { border: 1px solid #000; background: #fff; color: #000; padding: 4px 10px; cursor: pointer; }
</style>
