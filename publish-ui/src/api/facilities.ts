import request from '../utils/request'
import type { ApiResponse } from '../utils/request'

// 设施类型
export type FacilityType = 'factory' | 'line' | 'station'

// 设施状态
export type FacilityStatus = 'active' | 'inactive'

// 设施节点
export interface FacilityNode {
  id: string
  name: string
  type: FacilityType
  code?: string
  description?: string
  location?: string
  status: FacilityStatus
  ip?: string
  mac?: string
  createTime: string
  updateTime: string
  children?: FacilityNode[]
}

// 厂区创建请求
export interface CreateFactoryRequest {
  name: string
  code?: string
  description?: string
  location?: string
  status?: FacilityStatus
}

// 线体创建请求
export interface CreateLineRequest {
  factoryId: string
  name: string
  code?: string
  description?: string
  status?: FacilityStatus
}

// 工位创建请求
export interface CreateStationRequest {
  lineId: string
  name: string
  code?: string
  description?: string
  ip?: string
  mac?: string
  status?: FacilityStatus
}

// 更新请求
export interface UpdateFactoryRequest {
  name?: string
  code?: string
  description?: string
  status?: FacilityStatus
  location?: string
}

export interface UpdateLineRequest {
  name?: string
  code?: string
  description?: string
  status?: FacilityStatus
}

export interface UpdateStationRequest {
  name?: string
  code?: string
  description?: string
  status?: FacilityStatus
  ip?: string
  mac?: string
}

// 获取设施树
export function getFacilitiesTree(search?: string) {
  return request<ApiResponse<FacilityNode[]>>({
    url: '/facilities/tree',
    method: 'get',
    params: { search }
  })
}

// 创建厂区
export function createFactory(data: CreateFactoryRequest) {
  return request<ApiResponse<FacilityNode>>({
    url: '/facilities/factory',
    method: 'post',
    data
  })
}

// 创建线体
export function createLine(data: CreateLineRequest) {
  return request<ApiResponse<FacilityNode>>({
    url: '/facilities/line',
    method: 'post',
    data
  })
}

// 创建工位
export function createStation(data: CreateStationRequest) {
  return request<ApiResponse<FacilityNode>>({
    url: '/facilities/station',
    method: 'post',
    data
  })
}

// 更新厂区
export function updateFactory(id: string, data: UpdateFactoryRequest) {
  return request<ApiResponse<FacilityNode>>({
    url: `/facilities/factory/${id}`,
    method: 'put',
    data
  })
}

// 更新线体
export function updateLine(id: string, data: UpdateLineRequest) {
  return request<ApiResponse<FacilityNode>>({
    url: `/facilities/line/${id}`,
    method: 'put',
    data
  })
}

// 更新工位
export function updateStation(id: string, data: UpdateStationRequest) {
  return request<ApiResponse<FacilityNode>>({
    url: `/facilities/station/${id}`,
    method: 'put',
    data
  })
}

// 删除厂区
export function deleteFactory(id: string) {
  return request<ApiResponse<null>>({
    url: `/facilities/factory/${id}`,
    method: 'delete'
  })
}

// 删除线体
export function deleteLine(id: string) {
  return request<ApiResponse<null>>({
    url: `/facilities/line/${id}`,
    method: 'delete'
  })
}

// 删除工位
export function deleteStation(id: string) {
  return request<ApiResponse<null>>({
    url: `/facilities/station/${id}`,
    method: 'delete'
  })
}

// 工位搜索响应
export interface StationSearchResult {
  id: string
  name: string
  code?: string
  description?: string
  ip?: string
  mac?: string
  status: FacilityStatus
  path: string
  factoryId: string
  factoryName: string
  lineId: string
  lineName: string
  createTime: string
  updateTime: string
}

// 工位搜索请求参数
export interface SearchStationsParams {
  keyword?: string
  page?: number
  pageSize?: number
}

// 工位搜索
export function searchStations(params: SearchStationsParams = {}) {
  return request<ApiResponse<{
    list: StationSearchResult[]
    total: number
    page: number
    pageSize: number
  }>>({
    url: '/facilities/stations/search',
    method: 'get',
    params
  })
}

