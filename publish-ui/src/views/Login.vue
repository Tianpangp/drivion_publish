<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Logo 和标题 -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-lg mb-4">
          <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-gray-800 mb-2">{{ t('login.title') }}</h1>
        <p class="text-gray-500">{{ t('login.subtitle') }}</p>
      </div>

      <!-- 登录表单 -->
      <div class="bg-white rounded-2xl shadow-xl p-8">
        <a-form
          :model="formState"
          @finish="handleLogin"
          layout="vertical"
          class="space-y-4"
        >
          <a-form-item
            :label="t('login.username')"
            name="username"
            :rules="[{ required: true, message: t('login.usernamePlaceholder') }]"
          >
            <a-input
              v-model:value="formState.username"
              size="large"
              :placeholder="t('login.usernamePlaceholder')"
              class="rounded-lg"
            >
              <template #prefix>
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </template>
            </a-input>
          </a-form-item>

          <a-form-item
            :label="t('login.password')"
            name="password"
            :rules="[{ required: true, message: t('login.passwordPlaceholder') }]"
          >
            <a-input-password
              v-model:value="formState.password"
              size="large"
              :placeholder="t('login.passwordPlaceholder')"
              class="rounded-lg"
            >
              <template #prefix>
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </template>
            </a-input-password>
          </a-form-item>

          <div class="flex items-center justify-between">
            <a-checkbox v-model:checked="formState.remember">
              {{ t('login.remember') }}
            </a-checkbox>
            <a href="#" class="text-sm text-blue-600 hover:text-blue-500">忘记密码?</a>
          </div>

          <a-button
            type="primary"
            html-type="submit"
            size="large"
            :loading="loading"
            class="w-full rounded-lg h-12 bg-gradient-to-r from-blue-500 to-blue-600 border-0 hover:from-blue-600 hover:to-blue-700 shadow-md"
          >
            {{ t('login.login') }}
          </a-button>
        </a-form>

        <div class="mt-6 text-center text-sm text-gray-600">还没有账号？<router-link to="/register" class="text-blue-600 ml-1">立即注册</router-link></div>
      </div>

      <!-- 语言切换 -->
      <div class="mt-6 text-center">
        <a-dropdown>
          <a class="text-gray-500 hover:text-gray-700 text-sm inline-flex items-center gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
            </svg>
            {{ currentLocale === 'zh-CN' ? '简体中文' : 'English' }}
          </a>
          <template #overlay>
            <a-menu @click="handleLocaleChange">
              <a-menu-item key="zh-CN">简体中文</a-menu-item>
              <a-menu-item key="en-US">English</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { useUserStore } from '../stores/user'
import type { MenuInfo } from 'ant-design-vue/es/menu/src/interface'

const router = useRouter()
const { t, locale } = useI18n()
const userStore = useUserStore()

const currentLocale = computed(() => locale.value)

const formState = reactive({
  username: '',
  password: '',
  remember: false
})

const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  try {
    await userStore.login(formState.username, formState.password)
    message.success(t('login.loginSuccess'))
    router.push('/')
  } catch (error) {
    message.error(t('login.loginFailed'))
  } finally {
    loading.value = false
  }
}

const handleLocaleChange = (e: MenuInfo) => {
  locale.value = e.key as string
  localStorage.setItem('locale', e.key as string)
}
</script>
