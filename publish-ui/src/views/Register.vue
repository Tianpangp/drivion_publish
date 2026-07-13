<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-white border border-gray-200 shadow-sm rounded-lg p-8">
      <h1 class="text-2xl font-semibold text-gray-900">注册发布系统账号</h1>
      <p class="text-sm text-gray-500 mt-2 mb-6">新账号默认具有只读查看权限。</p>
      <a-form :model="form" layout="vertical" @finish="submit">
        <a-form-item label="用户名" name="username" :rules="[{ required: true, min: 3, message: '请输入至少 3 位用户名' }]">
          <a-input v-model:value="form.username" autocomplete="username" />
        </a-form-item>
        <a-form-item label="昵称" name="nickname"><a-input v-model:value="form.nickname" /></a-form-item>
        <a-form-item label="邮箱" name="email"><a-input v-model:value="form.email" type="email" /></a-form-item>
        <a-form-item label="密码" name="password" :rules="[{ required: true, min: 6, message: '密码至少 6 位' }]">
          <a-input-password v-model:value="form.password" autocomplete="new-password" />
        </a-form-item>
        <a-form-item label="确认密码" name="confirmPassword" :rules="[{ required: true, validator: validateConfirm }]">
          <a-input-password v-model:value="form.confirmPassword" autocomplete="new-password" />
        </a-form-item>
        <a-button type="primary" html-type="submit" block :loading="loading">注册</a-button>
      </a-form>
      <div class="text-center mt-5"><router-link to="/login" class="text-blue-600">返回登录</router-link></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import * as authApi from '../api/auth'

const router = useRouter()
const loading = ref(false)
const form = reactive({ username: '', nickname: '', email: '', password: '', confirmPassword: '' })
const validateConfirm = async (_rule: unknown, value: string) => {
  if (!value) return Promise.reject('请再次输入密码')
  if (value !== form.password) return Promise.reject('两次输入的密码不一致')
  return Promise.resolve()
}
const submit = async () => {
  loading.value = true
  try {
    await authApi.register({ username: form.username, password: form.password, nickname: form.nickname || undefined, email: form.email || undefined })
    message.success('注册成功，请登录')
    router.push('/login')
  } finally { loading.value = false }
}
</script>
