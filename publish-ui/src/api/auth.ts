import request from '../utils/request'
import type { ApiResponse } from '../utils/request'

// 用户信息
export interface UserInfo {
  id: string
  username: string
  nickname?: string
  role: RoleCode
  email?: string
  avatar?: string
  permissions: string[]
  roles?: string[]
  authMode?: 'local' | 'sso'
}

export interface AuthModeInfo {
  mode: 'local' | 'sso'
  registrationEnabled: boolean
  ssoLoginUrl?: string
}

export type RoleCode = 'admin' | 'developer' | 'tester' | 'release_manager' | 'engineer' | 'viewer'

export interface RoleInfo { code: RoleCode; name: string; description?: string }
export interface UserListItem extends Omit<UserInfo, 'permissions'> { status: 'active' | 'inactive'; createTime: string; updateTime: string }
export interface RoleRequestItem {
  id: string; userId: string; username: string; nickname?: string; currentRole: RoleCode
  requestedRole: RoleCode; reason?: string; status: string; createdAt: string; reviewComment?: string
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

export function getAuthMode() {
  return request<ApiResponse<AuthModeInfo>>({ url: '/auth/mode', method: 'get' })
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
  return request<ApiResponse<{ list: UserListItem[]; total: number; page: number; pageSize: number }>>({
    url: '/auth/users/search',
    method: 'get',
    params
  })
}

export function getRoles() {
  return request<ApiResponse<RoleInfo[]>>({ url: '/auth/roles', method: 'get' })
}

export function updateProfile(data: { nickname?: string; email?: string }) {
  return request<ApiResponse<UserInfo>>({ url: '/auth/profile', method: 'put', data })
}

export function changePassword(data: { oldPassword: string; newPassword: string }) {
  return request<ApiResponse<null>>({ url: '/auth/password', method: 'put', data })
}

export function deleteAccount(password: string) {
  return request<ApiResponse<null>>({ url: '/auth/account', method: 'delete', data: { password } })
}

export function applyRole(role: RoleCode, reason?: string) {
  return request<ApiResponse<{ id: string; status: string }>>({ url: '/auth/role-requests', method: 'post', data: { role, reason } })
}

export function getMyRoleRequests() {
  return request<ApiResponse<RoleRequestItem[]>>({ url: '/auth/role-requests/me', method: 'get' })
}

export function getRoleRequests(status = 'pending') {
  return request<ApiResponse<RoleRequestItem[]>>({ url: '/auth/role-requests', method: 'get', params: { status } })
}

export function reviewRoleRequest(id: string, decision: 'approve' | 'reject', comment?: string) {
  return request<ApiResponse<null>>({ url: `/auth/role-requests/${id}/${decision}`, method: 'post', data: { comment } })
}

export function changeUserRole(id: string, role: RoleCode) {
  return request<ApiResponse<null>>({ url: `/auth/users/${id}/role`, method: 'put', data: { role } })
}

export function changeUserStatus(id: string, status: 'active' | 'inactive') {
  return request<ApiResponse<null>>({ url: `/auth/users/${id}/status`, method: 'put', data: { status } })
}
