import request from '../utils/request'
import type { ApiResponse, PageResponse } from '../utils/request'

// 驱动类型
export type DriverType = 'java' | 'python' | 'cpp'

// 驱动包状态
export type DriverStatus = 'pending_testing' | 'testing' | 'pending_publish' | 'pending_remove' | 'published' | 'removed'

// 旧字段兼容：HAL 驱动包不再绑定设备
export interface BoundStation {
  id: string
  name: string
  code: string
}

// 驱动包信息
export interface DriverPackage {
  id: string
  name: string
  fileName: string
  type: DriverType
  version: string
  size: number
  uploadTime: string
  uploadUser: string
  status: DriverStatus
  description?: string
  boundStations: BoundStation[]
  protocol?: string
  manufacturer?: string
  deviceModel?: string
  downloadCount: number
  md5: string
  sha256?: string
  supportedPlatforms?: string[]
  apiDocUrl?: string
  readme?: string
  publishTime?: string
  deleted?: 0 | 1
  locked?: boolean
  storageProvider?: string
  storagePath?: string
}

// 驱动包列表查询参数
export interface DriverListParams {
  page?: number
  pageSize?: number
  search?: string
  type?: DriverType
  status?: DriverStatus
}

// 上传驱动包参数
export interface UploadDriverParams {
  file: File
}

// 获取驱动包列表
export function getDriverPackages(params: DriverListParams) {
  return request<ApiResponse<PageResponse<DriverPackage>>>({
    url: '/publish/drivers/packages',
    method: 'get',
    params
  })
}

// 上传驱动包
export function uploadDriverPackage(params: UploadDriverParams) {
  const formData = new FormData()
  formData.append('file', params.file)

  return request<ApiResponse<DriverPackage>>({
    url: '/publish/drivers/packages/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function replaceDriverPackage(id: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request<ApiResponse<DriverPackage>>({
    url: `/publish/drivers/packages/${id}/upload`, method: 'put', data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function deleteDriverPackage(id: string) {
  return request<ApiResponse<null>>({ url: `/publish/drivers/packages/${id}`, method: 'delete' })
}

export function submitDriverTesting(id: string) {
  return request<ApiResponse<DriverPackage>>({
    url: `/publish/drivers/packages/${id}/submit-testing`,
    method: 'post'
  })
}

export function submitDriverPublish(id: string) {
  return request<ApiResponse<DriverPackage>>({
    url: `/publish/drivers/packages/${id}/submit-publish`,
    method: 'post'
  })
}

export function submitDriverRemove(id: string) {
  return request<ApiResponse<DriverPackage>>({
    url: `/publish/drivers/packages/${id}/submit-remove`,
    method: 'post'
  })
}

export function rejectDriverPackage(id: string) {
  return request<ApiResponse<null>>({
    url: `/publish/drivers/packages/${id}/reject`,
    method: 'post'
  })
}

// 下载驱动包
export function downloadDriverPackage(id: string) {
  return request({
    url: `/publish/drivers/packages/${id}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

// 获取驱动包详情
export function getDriverPackageDetail(id: string) {
  return request<ApiResponse<DriverPackage>>({
    url: `/publish/drivers/packages/${id}`,
    method: 'get'
  })
}
