<template>
  <div class="h-screen flex flex-col bg-gray-50">
    <!-- 顶部导航栏 -->
    <header class="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <div>
            <h1 class="text-xl font-semibold text-gray-800" style="margin: 0;">{{ t('login.title') }}</h1>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <!-- 语言切换 -->
        <a-dropdown>
          <div class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors">
            <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
            </svg>
            <span class="text-sm text-gray-700">{{ currentLocale === 'zh-CN' ? '中文' : 'English' }}</span>
          </div>
          <template #overlay>
            <a-menu @click="handleLocaleChange">
              <a-menu-item key="zh-CN">简体中文</a-menu-item>
              <a-menu-item key="en-US">English</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>

        <!-- 用户信息 -->
        <a-dropdown>
          <div class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors">
            <div class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium">
              {{ userStore.user?.username?.[0]?.toUpperCase() }}
            </div>
            <div class="text-sm">
              <div class="text-gray-800 font-medium">{{ userStore.user?.username }}</div>
              <div class="text-gray-500 text-xs">{{ roleLabels[userStore.user?.role || 'viewer'] }}</div>
            </div>
          </div>
          <template #overlay>
            <a-menu>
              <a-menu-item key="profile" @click="router.push('/profile')">
                <div class="flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  {{ t('nav.profile') }}
                </div>
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item key="logout" @click="handleLogout">
                <div class="flex items-center gap-2 text-red-600">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  {{ t('nav.logout') }}
                </div>
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <!-- 侧边栏 -->
      <aside class="w-64 bg-white border-r border-gray-200 overflow-y-auto">
        <nav class="p-4 space-y-1">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group"
            :class="isActive(item.path) ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'"
          >
            <component :is="registeredIcons[item.icon]" class="w-5 h-5" />
            <span class="font-medium">{{ t(`nav.${item.name}`) }}</span>
          </router-link>
        </nav>
      </aside>

      <!-- 主内容区 -->
      <main class="flex-1 overflow-y-auto bg-gray-50">
        <div class="p-6">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '../stores/user'
import { message } from 'ant-design-vue'
import type { MenuInfo } from 'ant-design-vue/es/menu/src/interface'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const userStore = useUserStore()

const currentLocale = computed(() => locale.value)

const rawMenuItems = [
  {
    name: 'equipment',
    path: '/equipment',
    icon: 'equipment'
  },
  {
    name: 'facilities',
    path: '/facilities',
    icon: 'factory'
  },
  {
    name: 'drivers',
    path: '/drivers',
    icon: 'driver'
  },
  {
    name: 'autounit',
    path: '/autounit',
    icon: 'package'
  },
  {
    name: 'approvals',
    path: '/approvals',
    icon: 'approval',
    permissions: ['approval:test:view', 'approval:release:view']
  },
  {
    name: 'logs',
    path: '/logs',
    icon: 'log',
    permissions: ['log:view']
  },
  {
    name: 'users',
    path: '/users',
    icon: 'users',
    permissions: ['user:manage']
  }
] as const

const menuItems = computed(() => rawMenuItems.filter(item => !('permissions' in item) || userStore.hasAnyPermission([...item.permissions])))
const roleLabels: Record<string, string> = { admin: '系统管理员', developer: '开发人员', tester: '测试人员', release_manager: '发布管理员', engineer: '现场工程师', viewer: '查看人员' }

const isActive = (path: string) => {
  return route.path === path
}

const handleLocaleChange = (e: MenuInfo) => {
  locale.value = e.key as string
  localStorage.setItem('locale', e.key as string)
  message.success(locale.value === 'zh-CN' ? '语言已切换' : 'Language changed')
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
  message.success(t('nav.logout'))
}

// 图标组件
const IconEquipment = {
  template: `
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9h8M8 15h8M9 3v3m6-3v3M9 18v3m6-3v3M5 7a2 2 0 012-2h10a2 2 0 012 2v10a2 2 0 01-2 2H7a2 2 0 01-2-2V7z" />
    </svg>
  `
}

const IconFactory = {
  template: `
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  `
}

const IconDriver = {
  template: `
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
    </svg>
  `
}

const IconPackage = {
  template: `
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    </svg>
  `
}

const IconApproval = {
  template: `
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-5M7 3h10a2 2 0 012 2v14l-4-2-3 2-3-2-4 2V5a2 2 0 012-2z" />
    </svg>
  `
}

const IconLog = {
  template: `
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  `
}

const IconUsers = {
  template: `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a4 4 0 00-4-4h-1M9 20H2v-2a4 4 0 014-4h3m4-4a4 4 0 10-8 0 4 4 0 008 0zm8 0a3 3 0 11-6 0 3 3 0 016 0z" /></svg>`
}

const registeredIcons = {
  equipment: IconEquipment,
  factory: IconFactory,
  driver: IconDriver,
  package: IconPackage,
  approval: IconApproval,
  log: IconLog,
  users: IconUsers
}
</script>
