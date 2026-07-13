import request from '../utils/request'
import type { ApiResponse } from '../utils/request'
import type { AutoUnitPackage } from './autounit'

export type PackageStatus = 'pending_testing' | 'testing' | 'pending_publish' | 'pending_remove' | 'published' | 'removed'

export interface AutoUnitBinding {
  id: string
  name: string
  packageId: string
  version: string
  module: string
  status: PackageStatus
  boundAt: string
}

export interface EquipmentRow {
  id: string
  name: string
  code: string
  path: string
  type: string
  vendor: string
  model: string
  enabled: boolean
  binding?: AutoUnitBinding
  history: Array<Record<string, string>>
}

export interface ApprovalRow {
  id: string
  type: 'AutoUnit' | 'HAL'
  name: string
  packageId: string
  version: string
  action: '提交测试' | '提交发布' | '重新上架' | '申请下架'
  applicant: string
  submittedAt: string
  status: '待审批'
}

export function getEquipment() {
  return request<ApiResponse<EquipmentRow[]>>({
    url: '/publish/equipment',
    method: 'get'
  })
}

export function bindEquipmentAutoUnit(equipmentId: string, packageVersionId: string) {
  return request<ApiResponse<AutoUnitBinding>>({
    url: `/publish/equipment/${equipmentId}/autounit-binding`,
    method: 'post',
    data: { packageVersionId }
  })
}

export function unbindEquipmentAutoUnit(equipmentId: string) {
  return request<ApiResponse<null>>({
    url: `/publish/equipment/${equipmentId}/autounit-binding`,
    method: 'delete'
  })
}

export function getAutoUnitPackageOptions() {
  return request<ApiResponse<{ list: AutoUnitPackage[]; total: number; page: number; pageSize: number }>>({
    url: '/publish/autounit/packages',
    method: 'get',
    params: { page: 1, pageSize: 100 }
  })
}

export function getApprovals(type?: string) {
  return request<ApiResponse<ApprovalRow[]>>({
    url: '/publish/approvals',
    method: 'get',
    params: { type }
  })
}

export function approve(approvalId: string) {
  return request<ApiResponse<null>>({
    url: `/publish/approvals/${approvalId}/approve`,
    method: 'post'
  })
}

export function reject(approvalId: string) {
  return request<ApiResponse<null>>({
    url: `/publish/approvals/${approvalId}/reject`,
    method: 'post'
  })
}
