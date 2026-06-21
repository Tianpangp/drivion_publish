import axios from 'axios'
import type { AxiosInstance, AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { message } from 'ant-design-vue'
import router from '../router'

// API 基础路径
// 开发环境: 通过 Vite 代理到 localhost:8000
// 生产环境: 使用环境变量或默认值
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/publish/api/v1'

// 统一响应格式
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 分页响应格式
export interface PageResponse<T = any> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

// 创建 axios 实例
const service: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  withCredentials: true // 允许携带 Cookie
})

// 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    
    if (token && config.headers) {
      // 首次请求使用 Authorization 头
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error: AxiosError) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>): Promise<any> => {
    // 如果是 blob 类型的响应（文件下载），直接返回完整响应对象
    if (response.config.responseType === 'blob') {
      return Promise.resolve(response)
    }
    
    const res = response.data
    
    // 如果响应码不是 200，则判定为错误
    if (res.code !== 200) {
      message.error(res.message || '请求失败')
      
      // 401: 未认证或认证失败
      if (res.code === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
      }
      
      // 403: 无权限
      if (res.code === 403) {
        message.error('无权限访问')
      }
      
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    
    return Promise.resolve(res)
  },
  (error: AxiosError<ApiResponse>) => {
    console.error('响应错误:', error)
    
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          message.error('未登录或登录已过期')
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          router.push('/login')
          break
        case 403:
          message.error('无权限访问')
          break
        case 404:
          message.error('请求的资源不存在')
          break
        case 500:
          message.error('服务器内部错误')
          break
        default:
          message.error(data?.message || '请求失败')
      }
    } else if (error.request) {
      message.error('网络错误，请检查网络连接')
    } else {
      message.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

export default service

