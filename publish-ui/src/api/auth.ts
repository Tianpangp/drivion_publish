import request from '../utils/request'
import type { ApiResponse } from '../utils/request'

// 用户信息
export interface UserInfo {
  id: string
  username: string
  nickname?: string
  role: 'admin' | 'user'
  email?: string
  avatar?: string
  permissions: string[]
}

// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应
export interface LoginResponse {
  token: string
  userInfo: UserInfo
  expiresIn: number
}

// 注册请求
export interface RegisterRequest {
  username: string
  password: string
  nickname?: string
  email?: string
}

// 用户搜索
export interface UserSearchParams {
  keyword?: string
  role?: string
  status?: string
  page?: number
  pageSize?: number
}

// 用户登录
export function login(data: LoginRequest) {
  return request<ApiResponse<LoginResponse>>({
    url: '/auth/login',
    method: 'post',
    data
  })
}

// 用户注册
export function register(data: RegisterRequest) {
  return request<ApiResponse<UserInfo>>({
    url: '/auth/register',
    method: 'post',
    data
  })
}

// 用户登出
export function logout() {
  return request<ApiResponse<null>>({
    url: '/auth/logout',
    method: 'post'
  })
}

// 获取当前用户信息
export function getUserInfo() {
  return request<ApiResponse<UserInfo>>({
    url: '/auth/userInfo',
    method: 'get'
  })
}

// 用户列表搜索
export function searchUsers(params: UserSearchParams) {
  return request({
    url: '/auth/users/search',
    method: 'get',
    params
  })
}

