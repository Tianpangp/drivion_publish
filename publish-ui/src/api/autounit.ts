import request from '../utils/request'
import type { ApiResponse, PageResponse } from '../utils/request'

// AutoUnit 包状态
export type AutoUnitStatus = 'pending_testing' | 'testing' | 'pending_publish' | 'pending_remove' | 'published' | 'removed'

// 绑定的设备
export interface BoundEquipment {
  id: string
  name: string
  code: string
}

// AutoUnit 包信息
export interface AutoUnitPackage {
  id: string
  name: string
  packageId?: string
  fileName: string
  version: string
  module?: string
  size: number
  uploadTime: string
  uploadUser: string
  status: AutoUnitStatus
  description?: string
  boundStations: BoundEquipment[]
  dependencies: string[]
  pythonVersion: string
  downloadCount: number
  md5: string
  sha256: string
  readme?: string
  changelog?: string
  publishTime?: string
  publishUser?: string
  deleted?: 0 | 1
  locked?: boolean
  storageProvider?: string
  storagePath?: string
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
}

// 获取 AutoUnit 包列表
export function getAutoUnitPackages(params: AutoUnitListParams) {
  return request<ApiResponse<PageResponse<AutoUnitPackage>>>({
    url: '/publish/autounit/packages',
    method: 'get',
    params
  })
}

// 上传 AutoUnit 包
export function uploadAutoUnitPackage(params: UploadAutoUnitParams) {
  const formData = new FormData()
  formData.append('file', params.file)

  return request<ApiResponse<AutoUnitPackage>>({
    url: '/publish/autounit/packages/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function replaceAutoUnitPackage(id: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request<ApiResponse<AutoUnitPackage>>({
    url: `/publish/autounit/packages/${id}/upload`, method: 'put', data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function deleteAutoUnitPackage(id: string) {
  return request<ApiResponse<null>>({ url: `/publish/autounit/packages/${id}`, method: 'delete' })
}

export function submitAutoUnitTesting(id: string) {
  return request<ApiResponse<AutoUnitPackage>>({
    url: `/publish/autounit/packages/${id}/submit-testing`,
    method: 'post'
  })
}

export function submitAutoUnitPublish(id: string) {
  return request<ApiResponse<AutoUnitPackage>>({
    url: `/publish/autounit/packages/${id}/submit-publish`,
    method: 'post'
  })
}

export function submitAutoUnitRemove(id: string) {
  return request<ApiResponse<AutoUnitPackage>>({
    url: `/publish/autounit/packages/${id}/submit-remove`,
    method: 'post'
  })
}

export function rejectAutoUnitPackage(id: string) {
  return request<ApiResponse<null>>({
    url: `/publish/autounit/packages/${id}/reject`,
    method: 'post'
  })
}

// 下载 AutoUnit 包
export function downloadAutoUnitPackage(id: string) {
  return request({
    url: `/publish/autounit/packages/${id}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

// 获取 AutoUnit 包详情
export function getAutoUnitPackageDetail(id: string) {
  return request<ApiResponse<AutoUnitPackage>>({
    url: `/publish/autounit/packages/${id}`,
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
