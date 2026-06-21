import request from '../utils/request'
import type { ApiResponse, PageResponse } from '../utils/request'

// 绑定的工位
export interface BoundStation {
  id: string
  name: string
  code: string
  path: string
}

// 界面信息
export interface InterfaceInfo {
  id: string
  name: string
  description?: string
  jsonFilePath?: string  // JSON文件在MinIO中的路径
  fileSize?: number      // 文件大小（字节）
  fileMd5?: string       // 文件MD5值
  thumbnail?: string     // 缩略图URL
  boundStations: BoundStation[]
  createTime: string
  updateTime: string
  createUser: string
  lastEditUser?: string
}

// 界面列表查询参数
export interface InterfaceListParams {
  page?: number
  pageSize?: number
  search?: string
}

// 上传界面请求
export interface UploadInterfaceParams {
  file: File           // JSON配置文件
  name: string        // 界面名称
  description?: string // 界面描述
  stationIds?: string[] // 初始绑定的工位ID列表
}

// 更新界面信息请求
export interface UpdateInterfaceInfoRequest {
  name?: string
  description?: string
  stationIds?: string[]  // 绑定的工位ID列表
}

// 获取界面列表
export function getInterfaces(params: InterfaceListParams) {
  return request<ApiResponse<PageResponse<InterfaceInfo>>>({
    url: '/interfaces',
    method: 'get',
    params
  })
}

// 上传界面（JSON文件）
export function uploadInterface(params: UploadInterfaceParams) {
  const formData = new FormData()
  formData.append('file', params.file)
  formData.append('name', params.name)
  if (params.description) formData.append('description', params.description)
  if (params.stationIds && params.stationIds.length > 0) {
    formData.append('stationIds', JSON.stringify(params.stationIds))
  }

  return request<ApiResponse<InterfaceInfo>>({
    url: '/interfaces',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 更新界面信息（不包括JSON文件）
export function updateInterfaceInfo(id: string, data: UpdateInterfaceInfoRequest) {
  return request<ApiResponse<InterfaceInfo>>({
    url: `/interfaces/${id}/info`,
    method: 'put',
    data
  })
}

// 删除界面
export function deleteInterface(id: string) {
  return request<ApiResponse<null>>({
    url: `/interfaces/${id}`,
    method: 'delete'
  })
}

// 获取界面详情
export function getInterfaceDetail(id: string) {
  return request<ApiResponse<InterfaceInfo>>({
    url: `/interfaces/${id}`,
    method: 'get'
  })
}

// 从 Content-Disposition 响应头中解析文件名
function getFileNameFromContentDisposition(disposition: string | null | undefined): string {
  if (!disposition) return 'interface.json'
  
  // 优先解析 RFC 5987 格式: filename*=UTF-8''encoded_filename
  const rfc5987Match = disposition.match(/filename\*=UTF-8''(.+?)(?:;|$)/i)
  if (rfc5987Match && rfc5987Match[1]) {
    try {
      return decodeURIComponent(rfc5987Match[1])
    } catch (e) {
      console.error('解码文件名失败:', e)
    }
  }
  
  // 备用: 解析传统格式 filename="xxx"
  const filenameMatch = disposition.match(/filename="?(.+?)"?(?:;|$)/i)
  if (filenameMatch && filenameMatch[1]) {
    return filenameMatch[1]
  }
  
  return 'interface.json'
}

// 下载界面JSON文件
export function downloadInterfaceJson(id: string) {
  return request({
    url: `/interfaces/${id}/download`,
    method: 'get',
    responseType: 'blob'
  }).then((response: any) => {
    // 从响应头获取文件名（支持中文）
    const disposition = response.headers?.['content-disposition']
    const filename = getFileNameFromContentDisposition(disposition)
    
    // 创建 Blob 并触发下载
    const blob = new Blob([response.data], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    return response
  })
}

// 预览界面
export function previewInterface(id: string) {
  return request<ApiResponse<any>>({
    url: `/interfaces/${id}/preview`,
    method: 'get'
  })
}

