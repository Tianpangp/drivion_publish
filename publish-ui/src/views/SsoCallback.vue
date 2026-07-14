<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center">
    <a-result v-if="error" status="error" title="SSO 登录失败" sub-title="登录状态无效或 SSO 服务暂时不可用。">
      <template #extra><a-button type="primary" @click="router.replace('/login')">返回登录</a-button></template>
    </a-result>
    <a-spin v-else size="large" tip="正在完成登录" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const error = ref(Boolean(route.query.error))

onMounted(async () => {
  if (error.value) return
  try {
    await userStore.loadAuthMode()
    await userStore.completeSsoLogin()
    await router.replace('/')
  } catch {
    error.value = true
  }
})
</script>
