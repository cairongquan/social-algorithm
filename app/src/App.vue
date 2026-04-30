<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

onMounted(() => {
  if (authStore.isAuthenticated) {
    authStore.fetchMe().catch(() => {
      authStore.logout()
      router.push('/login')
    })
  }
})

const showNavbar = computed(() => {
  return authStore.isAuthenticated && !['Login', 'Register'].includes(route.name as string)
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div id="app">
    <nav class="navbar" v-if="showNavbar">
      <div class="nav-brand">
        <router-link to="/">文章管理</router-link>
      </div>
      <div class="nav-links">
        <router-link to="/square" class="nav-link">广场</router-link>
        <router-link to="/topology" class="nav-link">拓扑</router-link>
        <router-link to="/tags" class="nav-link">标签管理</router-link>
        <router-link to="/profile" class="nav-link profile-link">
          <img v-if="authStore.avatarUrl" :src="authStore.avatarUrl" class="nav-avatar-img" alt="头像" />
          <span v-else class="nav-avatar-fallback">{{ authStore.avatarInitial }}</span>
          <span>{{ authStore.username || '用户' }}</span>
        </router-link>
        <button @click="handleLogout" class="btn-logout">退出登录</button>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: "Source Serif 4", Georgia, serif;
  background: #ffffff;
  color: #000000;
}

body::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: -1;
  opacity: 0.2;
  background-color: #f7f7f7;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140' viewBox='0 0 140 140'%3E%3Cg fill='none' stroke='%23959595' stroke-width='1.1' opacity='0.55'%3E%3Cpath d='M70 70 C70 52 56 38 38 38 C56 38 70 24 70 6 C70 24 84 38 102 38 C84 38 70 52 70 70 Z'/%3E%3Cpath d='M70 70 C70 88 56 102 38 102 C56 102 70 116 70 134 C70 116 84 102 102 102 C84 102 70 88 70 70 Z'/%3E%3Cpath d='M70 70 C52 70 38 56 38 38 C38 56 24 70 6 70 C24 70 38 84 38 102 C38 84 52 70 70 70 Z'/%3E%3Cpath d='M70 70 C88 70 102 56 102 38 C102 56 116 70 134 70 C116 70 102 84 102 102 C102 84 88 70 70 70 Z'/%3E%3Ccircle cx='70' cy='70' r='8'/%3E%3C/g%3E%3C/svg%3E");
  background-size: 140px 140px;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: #ffffff;
  border-bottom: 2px solid #000000;
}

.nav-brand a {
  color: #000000;
  text-decoration: none;
  font-size: 20px;
  font-weight: bold;
}

.nav-links {
  display: flex;
  gap: 16px;
  align-items: center;
}

.nav-link {
  color: #000000;
  text-decoration: none;
}

.profile-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.nav-avatar-img,
.nav-avatar-fallback {
  width: 28px;
  height: 28px;
  border: 1px solid #000000;
  border-radius: 50%;
  object-fit: cover;
}

.nav-avatar-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
}

.btn-logout {
  padding: 6px 12px;
  background: #000000;
  color: #ffffff;
  border: 1px solid #000000;
  cursor: pointer;
}

.main-content {
  min-height: calc(100vh - 60px);
}
</style>
