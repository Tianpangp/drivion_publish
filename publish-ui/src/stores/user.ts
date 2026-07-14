import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as authApi from '../api/auth'
import type { AuthModeInfo, UserInfo } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref<UserInfo | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const permissions = ref<string[]>([])
  const authMode = ref<AuthModeInfo>({ mode: 'local', registrationEnabled: true })

  const loadAuthMode = async () => {
    const response = await authApi.getAuthMode()
    authMode.value = response.data
    localStorage.setItem('authMode', response.data.mode)
    return response.data
  }

  // 登录
  const login = async (username: string, password: string) => {
    try {
      const response = await authApi.login({ username, password })
      const { token: newToken, userInfo, expiresIn } = response.data

      // 保存 token 和用户信息
      token.value = newToken
      user.value = userInfo
      permissions.value = userInfo.permissions

      localStorage.setItem('token', newToken)
      localStorage.setItem('user', JSON.stringify(userInfo))
      localStorage.setItem('tokenExpires', String(Date.now() + expiresIn * 1000))

      return response
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  const completeSsoLogin = async () => {
    const response = await authApi.getUserInfo()
    token.value = 'sso-session'
    user.value = response.data
    permissions.value = response.data.permissions
    localStorage.setItem('token', 'sso-session')
    localStorage.setItem('user', JSON.stringify(response.data))
    localStorage.removeItem('tokenExpires')
  }

  // 登出
  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('登出失败:', error)
    } finally {
      user.value = null
      token.value = null
      permissions.value = []
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('tokenExpires')
    }
  }

  const clearLocal = () => {
    user.value = null
    token.value = null
    permissions.value = []
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('tokenExpires')
  }

  const setUser = (value: UserInfo) => {
    user.value = value
    permissions.value = value.permissions
    localStorage.setItem('user', JSON.stringify(value))
  }

  // 加载用户信息
  const loadUser = async () => {
    const storedUser = localStorage.getItem('user')
    const storedToken = localStorage.getItem('token')
    const tokenExpires = localStorage.getItem('tokenExpires')

    // 检查 token 是否过期
    if (tokenExpires && Date.now() > Number(tokenExpires)) {
      // token 已过期,清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('tokenExpires')
      return
    }

    if (storedUser && storedToken) {
      user.value = JSON.parse(storedUser)
      token.value = storedToken
      permissions.value = user.value?.permissions || []

      // 尝试从服务器获取最新用户信息
      try {
        const response = await authApi.getUserInfo()
        user.value = response.data
        permissions.value = response.data.permissions
        localStorage.setItem('user', JSON.stringify(response.data))
      } catch (error) {
        console.error('获取用户信息失败:', error)
      }
    }
  }

  // 检查是否为管理员
  const isAdmin = () => {
    return user.value?.role === 'admin'
  }

  // 检查是否有某个权限
  const hasPermission = (permission: string) => {
    return permissions.value.includes(permission)
  }

  // 检查是否有任一权限
  const hasAnyPermission = (perms: string[]) => {
    return perms.some(p => permissions.value.includes(p))
  }

  // 检查是否有所有权限
  const hasAllPermissions = (perms: string[]) => {
    return perms.every(p => permissions.value.includes(p))
  }

  return {
    user,
    token,
    permissions,
    authMode,
    loadAuthMode,
    login,
    completeSsoLogin,
    logout,
    clearLocal,
    setUser,
    loadUser,
    isAdmin,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions
  }
})
