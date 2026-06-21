import request from '../utils/request'
import type { ApiResponse, PageResponse } from '../utils/request'

// 绑定的工位
export interface BoundStation {
  id: string
  name: string
  code: string
}

// 部署清单信息
export interface DeploymentManifest {
  id: string
  name: string
  description?: string
  fileName: string
  version: string
  size: number
  uploadTime: string
  uploadUser: string
  boundStations: BoundStation[]
  md5: string
  content?: string
  downloadCount?: number
}

// 部署清单列表查询参数
export interface ManifestListParams {
  page?: number
  pageSize?: number
  search?: string
}

// 上传部署清单参数
export interface UploadManifestParams {
  file: File
  name: string
  version?: string
  description?: string
}

// 更新部署清单信息
export interface UpdateManifestRequest {
  name?: string
  description?: string
  version?: string
}

// 获取部署清单列表
export function getDeploymentManifests(params: ManifestListParams) {
  return request<ApiResponse<PageResponse<DeploymentManifest>>>({
    url: '/deployment/manifests',
    method: 'get',
    params
  })
}

// 上传部署清单
export function uploadDeploymentManifest(params: UploadManifestParams) {
  const formData = new FormData()
  formData.append('file', params.file)
  formData.append('name', params.name)
  if (params.version) formData.append('version', params.version)
  if (params.description) formData.append('description', params.description)

  return request<ApiResponse<DeploymentManifest>>({
    url: '/deployment/manifests/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取部署清单详情
export function getDeploymentManifestDetail(id: string) {
  return request<ApiResponse<DeploymentManifest>>({
    url: `/deployment/manifests/${id}`,
    method: 'get'
  })
}

// 更新部署清单信息
export function updateDeploymentManifest(id: string, data: UpdateManifestRequest) {
  return request<ApiResponse<DeploymentManifest>>({
    url: `/deployment/manifests/${id}`,
    method: 'put',
    data
  })
}

// 删除部署清单
export function deleteDeploymentManifest(id: string) {
  return request<ApiResponse<null>>({
    url: `/deployment/manifests/${id}`,
    method: 'delete'
  })
}

// 下载部署清单
export function downloadDeploymentManifest(id: string) {
  return request({
    url: `/deployment/manifests/${id}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

// 绑定部署清单到工位
export function bindManifestToStations(id: string, stationIds: string[]) {
  return request<ApiResponse<any>>({
    url: `/deployment/manifests/${id}/bind`,
    method: 'post',
    data: { stationIds }
  })
}

// 解绑部署清单与工位
export function unbindManifestFromStations(id: string, stationIds: string[]) {
  return request<ApiResponse<null>>({
    url: `/deployment/manifests/${id}/bind`,
    method: 'delete',
    data: { stationIds }
  })
}

