import request from '../utils/request'
import type { ApiResponse } from '../utils/request'

// 工位绑定信息
export interface StationBindings {
  stationId: string
  stationName: string
  stationCode: string
  stationPath: string
  interfaces: Array<{
    id: string
    name: string
    layout: string
    bindTime: string
  }>
  deploymentManifests: Array<{
    id: string
    name: string
    version: string
    bindTime: string
  }>
  autounitPackages: Array<{
    id: string
    name: string
    version: string
    applyTime: string
  }>
}

// 绑定界面到工位
export function bindInterfaceToStations(interfaceId: string, stationIds: string[]) {
  return request<ApiResponse<any>>({
    url: '/bindings/interface',
    method: 'post',
    data: { interfaceId, stationIds }
  })
}

// 解绑界面与工位
export function unbindInterfaceFromStations(interfaceId: string, stationIds: string[]) {
  return request<ApiResponse<null>>({
    url: '/bindings/interface',
    method: 'delete',
    data: { interfaceId, stationIds }
  })
}

// 获取工位的所有绑定信息
export function getStationBindings(stationId: string) {
  return request<ApiResponse<StationBindings>>({
    url: `/stations/${stationId}/bindings`,
    method: 'get'
  })
}

