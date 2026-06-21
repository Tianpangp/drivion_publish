import request from '../utils/request'
import type { ApiResponse, PageResponse } from '../utils/request'

// AutoUnit 包状态
export type AutoUnitStatus = 'published' | 'unpublished' | 'testing'

// 绑定的工位
export interface BoundStation {
  id: string
  name: string
  code: string
}

// AutoUnit 包信息
export interface AutoUnitPackage {
  id: string
  name: string
  fileName: string
  version: string
  size: number
  uploadTime: string
  uploadUser: string
  status: AutoUnitStatus
  description?: string
  boundStations: BoundStation[]
  dependencies: string[]
  pythonVersion: string
  downloadCount: number
  md5: string
  sha256: string
  readme?: string
  changelog?: string
  publishTime?: string
  publishUser?: string
}

// AutoUnit 包列表查询参数
export interface AutoUnitListParams {
  page?: number
  pageSize?: number
  search?: string
  status?: AutoUnitStatus
}

// 上传 AutoUnit 包参数
export interface UploadAutoUnitParams {
  file: File
  name: string
  version: string
  description?: string
  pythonVersion?: string
}

// 获取 AutoUnit 包列表
export function getAutoUnitPackages(params: AutoUnitListParams) {
  return request<ApiResponse<PageResponse<AutoUnitPackage>>>({
    url: '/autounit/packages',
    method: 'get',
    params
  })
}

// 上传 AutoUnit 包
export function uploadAutoUnitPackage(params: UploadAutoUnitParams) {
  const formData = new FormData()
  formData.append('file', params.file)
  formData.append('name', params.name)
  formData.append('version', params.version)
  if (params.description) formData.append('description', params.description)
  if (params.pythonVersion) formData.append('pythonVersion', params.pythonVersion)

  return request<ApiResponse<AutoUnitPackage>>({
    url: '/autounit/packages/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 更新 AutoUnit 包状态
export function updateAutoUnitStatus(id: string, status: AutoUnitStatus) {
  return request<ApiResponse<AutoUnitPackage>>({
    url: `/autounit/packages/${id}/status`,
    method: 'put',
    data: { status }
  })
}

// 撤回 AutoUnit 包
export function recallAutoUnitPackage(id: string) {
  return request<ApiResponse<null>>({
    url: `/autounit/packages/${id}/recall`,
    method: 'delete'
  })
}

// 下载 AutoUnit 包
export function downloadAutoUnitPackage(id: string) {
  return request({
    url: `/autounit/packages/${id}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

// 获取 AutoUnit 包详情
export function getAutoUnitPackageDetail(id: string) {
  return request<ApiResponse<AutoUnitPackage>>({
    url: `/autounit/packages/${id}`,
    method: 'get'
  })
}

// 应用 AutoUnit 包到工位
export function applyAutoUnitToStations(id: string, stationIds: string[]) {
  return request<ApiResponse<any>>({
    url: `/autounit/packages/${id}/apply`,
    method: 'post',
    data: { stationIds }
  })
}

// 取消 AutoUnit 包在工位的应用
export function cancelAutoUnitFromStations(id: string, stationIds: string[]) {
  return request<ApiResponse<null>>({
    url: `/autounit/packages/${id}/apply`,
    method: 'delete',
    data: { stationIds }
  })
}

