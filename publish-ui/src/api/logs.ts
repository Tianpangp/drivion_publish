import request from '../utils/request'
import type { ApiResponse, PageResponse } from '../utils/request'

// 操作类型
export type OperationType = 'create' | 'update' | 'delete' | 'upload' | 'bind' | 'unbind'

// 操作结果
export type OperationResult = 'success' | 'failed'

// 操作模块
export type OperationModule = '厂区管理' | '线体管理' | '工位管理' | '驱动包管理' | 'AutoUnit包' | '界面管理' | '部署清单管理'

// 日志信息
export interface LogInfo {
  id: string
  operation: OperationType
  module: OperationModule
  operator: string
  operatorId: string
  role: string
  result: OperationResult
  time: string
  description: string
  ip: string
  userAgent: string
  changes?: any
  error?: string
  requestUrl?: string
  requestMethod?: string
  responseTime?: number
  targetId?: string
  targetType?: string
}

// 日志列表查询参数
export interface LogListParams {
  page?: number
  pageSize?: number
  search?: string
  operation?: OperationType
  result?: OperationResult
  startTime?: string
  endTime?: string
  module?: OperationModule
}

// 导出日志参数
export interface ExportLogsParams {
  filters?: {
    operation?: OperationType
    result?: OperationResult
    startTime?: string
    endTime?: string
    module?: OperationModule
  }
}

// 获取日志列表
export function getLogs(params: LogListParams) {
  return request<ApiResponse<PageResponse<LogInfo>>>({
    url: '/logs',
    method: 'get',
    params
  })
}

// 获取日志详情
export function getLogDetail(id: string) {
  return request<ApiResponse<LogInfo>>({
    url: `/logs/${id}`,
    method: 'get'
  })
}

// 导出日志
export function exportLogs(data: ExportLogsParams) {
  return request({
    url: '/logs/export',
    method: 'post',
    data,
    responseType: 'blob'
  })
}

