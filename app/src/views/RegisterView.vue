<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppInput from '@/components/AppInput.vue'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const success = ref('')

async function handleRegister() {
  error.value = ''
  success.value = ''
  try {
    await authStore.register({ username: username.value, password: password.value })
    success.value = '注册成功，请登录。'
    setTimeout(() => router.push('/login'), 1500)
  } catch (err) {
    error.value = '注册失败，用户名可能已存在。'
  }
}
</script>

<template>
  <div class="register-view">
    <div class="register-form">
      <h2>注册</h2>
      <div class="form-group">
        <label>用户名</label>
        <AppInput v-model="username" type="text" placeholder="请输入用户名" />
      </div>
      <div class="form-group">
        <label>密码</label>
        <AppInput v-model="password" type="password" placeholder="请输入密码" />
      </div>
      <button @click="handleRegister" class="btn-submit">注册</button>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="success" class="success">{{ success }}</p>
      <p class="switch-form">
        已有账号？<router-link to="/login">去登录</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.register-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #ffffff;
}

.register-form {
  background: #ffffff;
  padding: 32px;
  border: 2px solid #000000;
  width: 400px;
}

h2 {
  color: #000000;
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 4px;
  color: #333;
}

.btn-submit {
  width: 100%;
  padding: 10px;
  background: #000000;
  color: #ffffff;
  border: 1px solid #000000;
  cursor: pointer;
  margin-top: 16px;
}

.error {
  color: #000000;
  border-left: 3px solid #000000;
  padding-left: 8px;
  margin-top: 8px;
}

.success {
  color: #000000;
  border-left: 3px solid #000000;
  padding-left: 8px;
  margin-top: 8px;
}

.switch-form {
  margin-top: 16px;
  text-align: center;
}
</style>
