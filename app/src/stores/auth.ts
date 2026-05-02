import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { LoginRequest, RegisterRequest, UserProfileUpdate } from '@/types/user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const userId = ref<string | null>(localStorage.getItem('user_id'))
  const isAdmin = ref(localStorage.getItem('is_admin') === '1')
  const avatarUrl = ref<string | null>(localStorage.getItem('avatar_url'))

  const isAuthenticated = computed(() => !!token.value)
  const avatarInitial = computed(() => (username.value?.trim()?.[0] || '?').toUpperCase())

  async function login(data: LoginRequest) {
    const response = await authApi.login(data)
    token.value = response.access_token
    localStorage.setItem('token', response.access_token)
    await fetchMe()
  }

  async function register(data: RegisterRequest) {
    await authApi.register(data)
  }

  async function fetchMe() {
    if (!token.value) return
    const me = await authApi.me(token.value)
    userId.value = me.user_id
    username.value = me.username
    isAdmin.value = !!me.is_admin
    avatarUrl.value = me.avatar_url ?? null
    localStorage.setItem('user_id', me.user_id)
    localStorage.setItem('username', me.username)
    localStorage.setItem('is_admin', me.is_admin ? '1' : '0')
    if (me.avatar_url) {
      localStorage.setItem('avatar_url', me.avatar_url)
    } else {
      localStorage.removeItem('avatar_url')
    }
  }

  async function updateProfile(data: UserProfileUpdate) {
    if (!token.value) return
    const result = await authApi.updateProfile(token.value, data)
    token.value = result.access_token
    localStorage.setItem('token', result.access_token)
    await fetchMe()
  }

  async function uploadAvatar(file: File) {
    if (!token.value) return
    await authApi.uploadAvatar(token.value, file)
    await fetchMe()
  }

  function logout() {
    token.value = null
    username.value = null
    userId.value = null
    isAdmin.value = false
    avatarUrl.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('user_id')
    localStorage.removeItem('is_admin')
    localStorage.removeItem('avatar_url')
  }

  return {
    token,
    userId,
    isAdmin,
    username,
    avatarUrl,
    avatarInitial,
    isAuthenticated,
    login,
    register,
    fetchMe,
    updateProfile,
    uploadAvatar,
    logout
  }
})
