import request from '../utils/request'
import type { ApiResponse, PageResponse } from '../utils/request'

// 驱动类型
export type DriverType = 'java' | 'python' | 'cpp'

// 驱动包状态
export type DriverStatus = 'published' | 'unpublished' | 'testing'

// 绑定的工位
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
  type: DriverType
  name: string
  version: string
  description?: string
  protocol?: string
  manufacturer?: string
  deviceModel?: string
}

// 获取驱动包列表
export function getDriverPackages(params: DriverListParams) {
  return request<ApiResponse<PageResponse<DriverPackage>>>({
    url: '/drivers/packages',
    method: 'get',
    params
  })
}

// 上传驱动包
export function uploadDriverPackage(params: UploadDriverParams) {
  const formData = new FormData()
  formData.append('file', params.file)
  formData.append('type', params.type)
  formData.append('name', params.name)
  formData.append('version', params.version)
  if (params.description) formData.append('description', params.description)
  if (params.protocol) formData.append('protocol', params.protocol)
  if (params.manufacturer) formData.append('manufacturer', params.manufacturer)
  if (params.deviceModel) formData.append('deviceModel', params.deviceModel)

  return request<ApiResponse<DriverPackage>>({
    url: '/drivers/packages/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 发布驱动包
export function publishDriverPackage(id: string) {
  return request<ApiResponse<DriverPackage>>({
    url: `/drivers/packages/${id}/publish`,
    method: 'post'
  })
}

// 下架驱动包
export function unpublishDriverPackage(id: string) {
  return request<ApiResponse<DriverPackage>>({
    url: `/drivers/packages/${id}/unpublish`,
    method: 'post'
  })
}

// 撤回驱动包
export function recallDriverPackage(id: string) {
  return request<ApiResponse<null>>({
    url: `/drivers/packages/${id}/recall`,
    method: 'delete'
  })
}

// 下载驱动包
export function downloadDriverPackage(id: string) {
  return request({
    url: `/drivers/packages/${id}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

// 获取驱动包详情
export function getDriverPackageDetail(id: string) {
  return request<ApiResponse<DriverPackage>>({
    url: `/drivers/packages/${id}`,
    method: 'get'
  })
}

