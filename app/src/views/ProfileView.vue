<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppInput from '@/components/AppInput.vue'
import AppDialog from '@/components/AppDialog.vue'
import AppToast from '@/components/AppToast.vue'

const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const showDialog = ref(false)
const dialogTitle = ref('')
const dialogMessage = ref('')
const showToast = ref(false)
const toastMessage = ref('')

onMounted(async () => {
  await authStore.fetchMe()
  username.value = authStore.username || ''
})

async function saveProfile() {
  if (!username.value.trim()) {
    dialogTitle.value = '提示'
    dialogMessage.value = '用户名不能为空'
    showDialog.value = true
    return
  }

  try {
    await authStore.updateProfile({
      username: username.value.trim(),
      password: password.value.trim() || undefined
    })
    password.value = ''
    toastMessage.value = '用户信息更新成功'
    showToast.value = true
    window.setTimeout(() => {
      showToast.value = false
    }, 1800)
  } catch (error) {
    dialogTitle.value = '更新失败'
    dialogMessage.value = '请检查用户名是否重复，或稍后再试。'
    showDialog.value = true
  }
}

async function handleAvatarUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    await authStore.uploadAvatar(file)
    toastMessage.value = '头像上传成功'
    showToast.value = true
    window.setTimeout(() => {
      showToast.value = false
    }, 1800)
  } catch (error) {
    dialogTitle.value = '上传失败'
    dialogMessage.value = '头像上传失败，请重试。'
    showDialog.value = true
  } finally {
    target.value = ''
  }
}
</script>

<template>
  <div class="profile-view">
    <h1>编辑用户信息</h1>

    <div class="profile-card">
      <div class="avatar-section">
        <img v-if="authStore.avatarUrl" :src="authStore.avatarUrl" class="avatar-image" alt="用户头像" />
        <div v-else class="avatar-fallback">{{ authStore.avatarInitial }}</div>
        <label class="upload-label">
          上传自定义头像
          <input type="file" accept="image/*" class="hidden-file" @change="handleAvatarUpload" />
        </label>
      </div>

      <div class="form-group">
        <label>用户名</label>
        <AppInput v-model="username" type="text" placeholder="请输入用户名" />
      </div>

      <div class="form-group">
        <label>新密码（可选）</label>
        <AppInput v-model="password" type="password" placeholder="留空则不修改密码" />
      </div>

      <button class="btn-save" @click="saveProfile">保存修改</button>
    </div>

    <AppDialog
      v-model="showDialog"
      :title="dialogTitle"
      :message="dialogMessage"
      confirm-text="我知道了"
    />
    <AppToast v-model="showToast" :message="toastMessage" />
  </div>
</template>

<style scoped>
.profile-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px;
}

h1 {
  color: #000000;
  margin-bottom: 20px;
}

.profile-card {
  border: 1px solid #000000;
  background: #ffffff;
  padding: 20px;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
}

.avatar-image,
.avatar-fallback {
  width: 66px;
  height: 66px;
  border: 2px solid #000000;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  color: #000000;
  font-size: 30px;
  font-weight: 700;
}

.upload-label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #000000;
  background: #ffffff;
  color: #000000;
  padding: 8px 12px;
  cursor: pointer;
}

.hidden-file {
  display: none;
}

.form-group {
  margin-top: 12px;
}

label {
  display: block;
  margin-bottom: 4px;
}

.btn-save {
  margin-top: 16px;
  border: 1px solid #000000;
  background: #000000;
  color: #ffffff;
  padding: 10px 16px;
  cursor: pointer;
}
</style>
