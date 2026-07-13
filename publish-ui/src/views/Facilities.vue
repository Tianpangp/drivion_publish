<template>
  <div class="space-y-6">
    <!-- 页面标题和操作 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ t('facilities.title') }}</h1>
        <p class="text-gray-500 mt-1">管理厂区、线体、工位和设备的四级结构</p>
      </div>
      <div class="flex gap-3">
        <a-button v-if="canCreate('factory')" @click="showCreateModal('factory')">
          <template #icon>
            <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </template>
          {{ t('facilities.createFactory') }}
        </a-button>
      </div>
    </div>

    <!-- 搜索框 -->
    <div class="bg-white rounded-xl p-4 shadow-sm">
      <a-input-search v-model:value="searchText" :placeholder="t('common.search')" size="large" class="max-w-md"
        allow-clear>
        <template #prefix>
          <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </template>
      </a-input-search>
    </div>

    <!-- 树形结构 -->
    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <div class="p-6">
        <a-tree v-if="treeData.length > 0" :tree-data="filteredTreeData" :expanded-keys="expandedKeys"
          @expand="onExpand" class="facility-tree">
          <template #title="{ title, key, type }">
            <div class="facility-node flex items-center justify-between group">
              <div class="flex items-center gap-3">
                <span class="facility-node-icon" :class="getTypeColor(type)">
                  <component :is="getTypeIcon(type)" class="facility-svg-icon" />
                </span>
                <div>
                  <div class="font-medium text-gray-800">{{ title }}</div>
                  <div class="text-xs text-gray-500">{{ getTypeLabel(type) }}</div>
                </div>
              </div>
              <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <a-button v-if="type === 'factory' && canCreate('line')" size="small" type="link" @click.stop="showCreateModal('line', key)">
                  添加线体
                </a-button>
                <a-button v-if="type === 'line' && canCreate('station')" size="small" type="link" @click.stop="showCreateModal('station', key)">
                  添加工位
                </a-button>
                <a-button v-if="type === 'station' && canCreate('equipment')" size="small" type="link" @click.stop="showCreateModal('equipment', key)">
                  添加设备
                </a-button>
                <a-button v-if="canEdit(type)" size="small" type="link" @click.stop="handleEdit(key, type)">
                  {{ t('common.edit') }}
                </a-button>
                <a-button v-if="canDelete(type)" size="small" type="link" danger @click.stop="handleDelete(key, type)">
                  {{ t('common.delete') }}
                </a-button>
              </div>
            </div>
          </template>
        </a-tree>
        <a-empty v-else description="暂无数据，请创建厂区" />
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <a-modal v-model:open="modalVisible" :title="modalTitle" @ok="handleModalOk" @cancel="handleModalCancel"
      :confirmLoading="modalLoading">
      <a-form :model="formState" layout="vertical" class="mt-4">
        <a-form-item v-if="modalType === 'factory'" :label="t('facilities.factoryName')" name="name"
          :rules="[{ required: true, message: '请输入厂区名称' }]">
          <a-input v-model:value="formState.name" :placeholder="t('facilities.factoryName')" />
        </a-form-item>

        <a-form-item v-if="modalType === 'line'" :label="t('facilities.lineName')" name="name"
          :rules="[{ required: true, message: '请输入线体名称' }]">
          <a-input v-model:value="formState.name" :placeholder="t('facilities.lineName')" />
        </a-form-item>

        <a-form-item v-if="modalType === 'station'" :label="t('facilities.stationName')" name="name"
          :rules="[{ required: true, message: '请输入工位名称' }]">
          <a-input v-model:value="formState.name" :placeholder="t('facilities.stationName')" />
        </a-form-item>

        <a-form-item v-if="modalType === 'equipment'" :label="t('facilities.equipmentName')" name="name"
          :rules="[{ required: true, message: '请输入设备名称' }]">
          <a-input v-model:value="formState.name" :placeholder="t('facilities.equipmentName')" />
        </a-form-item>

        <a-form-item v-if="modalType === 'station'" :label="t('facilities.stationCode')" name="code">
          <a-input v-model:value="formState.code" placeholder="工位编号（可选）" />
        </a-form-item>

        <a-form-item v-if="modalType === 'equipment'" :label="t('facilities.equipmentCode')" name="code">
          <a-input v-model:value="formState.code" placeholder="设备编号（可选）" />
        </a-form-item>

        <a-form-item v-if="modalType === 'factory'" label="地址" name="location">
          <a-input v-model:value="formState.location" placeholder="厂区地址（可选）" />
        </a-form-item>

        <a-form-item v-if="modalType === 'station'" label="IP地址" name="ip">
          <a-input v-model:value="formState.ip" placeholder="工位设备IP（可选）" />
        </a-form-item>

        <a-form-item v-if="modalType === 'station'" label="MAC地址" name="mac">
          <a-input v-model:value="formState.mac" placeholder="工位设备MAC（可选）" />
        </a-form-item>

        <a-form-item v-if="modalType === 'equipment'" label="设备类型" name="equipmentType">
          <a-input v-model:value="formState.equipmentType" placeholder="例如：视觉检测、运动控制、IO" />
        </a-form-item>

        <div v-if="modalType === 'equipment'" class="grid grid-cols-2 gap-3">
          <a-form-item label="厂商" name="vendor">
            <a-input v-model:value="formState.vendor" placeholder="设备厂商" />
          </a-form-item>
          <a-form-item label="型号" name="model">
            <a-input v-model:value="formState.model" placeholder="设备型号" />
          </a-form-item>
        </div>

        <a-form-item :label="t('common.description')" name="description">
          <a-textarea v-model:value="formState.description" :placeholder="t('common.description')" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import type { TreeProps } from 'ant-design-vue'
import * as facilitiesApi from '../api/facilities'
import type { FacilityNode as ApiFacilityNode, FacilityType } from '../api/facilities'
import { useUserStore } from '../stores/user'

const { t } = useI18n()
const userStore = useUserStore()

const permissionPrefix: Record<FacilityType, string> = {
  factory: 'facility:factory',
  line: 'facility:line',
  station: 'facility:station',
  equipment: 'facility:equipment'
}
const canCreate = (type: FacilityType) => type === 'equipment'
  ? userStore.hasPermission('facility:equipment:manage')
  : userStore.hasPermission(`${permissionPrefix[type]}:create`)
const canEdit = (type: FacilityType) => type === 'equipment'
  ? userStore.hasPermission('facility:equipment:manage')
  : userStore.hasPermission(`${permissionPrefix[type]}:edit`)
const canDelete = (type: FacilityType) => type === 'equipment'
  ? userStore.hasPermission('facility:equipment:manage')
  : userStore.hasPermission(`${permissionPrefix[type]}:delete`)

interface FacilityNode {
  key: string
  title: string
  type: FacilityType
  description?: string
  code?: string
  location?: string
  ip?: string
  mac?: string
  vendor?: string
  model?: string
  equipmentType?: string
  status?: string
  children?: FacilityNode[]
}

// 设施数据
const treeData = ref<FacilityNode[]>([])
const loading = ref(false)

const searchText = ref('')
const expandedKeys = ref<string[]>([])
const modalVisible = ref(false)
const modalLoading = ref(false)
const modalType = ref<FacilityType>('factory')
const editingKey = ref<string | null>(null)
const parentKey = ref<string | null>(null)

const formState = reactive({
  name: '',
  code: '',
  description: '',
  location: '',
  ip: '',
  mac: '',
  vendor: '',
  model: '',
  equipmentType: '',
  status: 'active' as 'active' | 'inactive'
})

// 转换 API 数据为树形结构
const convertToTreeNode = (node: ApiFacilityNode): FacilityNode => {
  return {
    key: node.id,
    title: node.name,
    type: node.type,
    code: node.code,
    description: node.description,
    location: node.location,
    ip: node.ip,
    mac: node.mac,
    vendor: node.vendor,
    model: node.model,
    equipmentType: node.equipmentType,
    status: node.status,
    children: node.children?.map(convertToTreeNode)
  }
}

// 加载设施树
const loadFacilities = async () => {
  loading.value = true
  try {
    const response = await facilitiesApi.getFacilitiesTree(searchText.value)
    treeData.value = response.data.map(convertToTreeNode)
    // 默认展开第一层
    if (treeData.value.length > 0) {
      expandedKeys.value = [treeData.value[0]!.key]
    }
  } catch (error) {
    console.error('加载设施树失败:', error)
  } finally {
    loading.value = false
  }
}

// 初始化
onMounted(() => {
  loadFacilities()
})

// 过滤树数据
const filteredTreeData = computed(() => {
  if (!searchText.value) return treeData.value

  const filterTree = (nodes: FacilityNode[]): FacilityNode[] => {
    return nodes.reduce((acc: FacilityNode[], node) => {
      const matchesSearch = node.title.toLowerCase().includes(searchText.value.toLowerCase())
      const children = node.children ? filterTree(node.children) : []

      if (matchesSearch || children.length > 0) {
        acc.push({
          ...node,
          children: children.length > 0 ? children : node.children
        })
      }
      return acc
    }, [])
  }

  return filterTree(treeData.value)
})

const modalTitle = computed(() => {
  if (editingKey.value) {
    if (modalType.value === 'factory') return t('facilities.editFactory')
    if (modalType.value === 'line') return t('facilities.editLine')
    if (modalType.value === 'equipment') return t('facilities.editEquipment')
    return t('facilities.editStation')
  }
  if (modalType.value === 'factory') return t('facilities.createFactory')
  if (modalType.value === 'line') return t('facilities.createLine')
  if (modalType.value === 'equipment') return t('facilities.createEquipment')
  return t('facilities.createStation')
})

const onExpand: TreeProps['onExpand'] = (keys) => {
  expandedKeys.value = keys as string[]
}

const getTypeColor = (type: string) => {
  if (type === 'factory') return 'facility-icon-factory'
  if (type === 'line') return 'facility-icon-line'
  if (type === 'station') return 'facility-icon-station'
  return 'facility-icon-equipment'
}

const getTypeLabel = (type: string) => {
  if (type === 'factory') return t('facilities.factory')
  if (type === 'line') return t('facilities.line')
  if (type === 'station') return t('facilities.station')
  return t('facilities.equipment')
}

const getTypeIcon = (type: string) => {
  if (type === 'factory') return IconFactory
  if (type === 'line') return IconLine
  if (type === 'station') return IconStation
  return IconEquipment
}

const showCreateModal = (type: FacilityType, parent?: string) => {
  modalType.value = type
  editingKey.value = null
  parentKey.value = parent || null
  formState.name = ''
  formState.code = ''
  formState.description = ''
  formState.location = ''
  formState.ip = ''
  formState.mac = ''
  formState.vendor = ''
  formState.model = ''
  formState.equipmentType = ''
  formState.status = 'active'
  modalVisible.value = true
}

const handleEdit = (key: string, type: FacilityType) => {
  modalType.value = type
  editingKey.value = key

  // 查找节点数据
  const findNode = (nodes: FacilityNode[], targetKey: string): FacilityNode | null => {
    for (const node of nodes) {
      if (node.key === targetKey) return node
      if (node.children) {
        const found = findNode(node.children, targetKey)
        if (found) return found
      }
    }
    return null
  }

  const node = findNode(treeData.value, key)
  if (node) {
    formState.name = node.title
    formState.code = node.code || ''
    formState.description = node.description || ''
    formState.location = node.location || ''
    formState.ip = node.ip || ''
    formState.mac = node.mac || ''
    formState.vendor = node.vendor || ''
    formState.model = node.model || ''
    formState.equipmentType = node.equipmentType || ''
    formState.status = (node.status as 'active' | 'inactive') || 'active'
  }

  modalVisible.value = true
}

const handleDelete = async (key: string, type: string) => {
  Modal.confirm({
    title: t('facilities.deleteConfirm'),
    content: `确认删除此${getTypeLabel(type)}吗？`,
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    okType: 'danger',
    onOk: async () => {
      try {
        if (type === 'factory') {
          await facilitiesApi.deleteFactory(key)
        } else if (type === 'line') {
          await facilitiesApi.deleteLine(key)
        } else if (type === 'equipment') {
          await facilitiesApi.deleteEquipment(key)
        } else {
          await facilitiesApi.deleteStation(key)
        }
        message.success(t('facilities.deleteSuccess'))
        await loadFacilities()
      } catch (error) {
        console.error('删除失败:', error)
      }
    }
  })
}

const handleModalOk = async () => {
  if (!formState.name) {
    message.error('请填写必填项')
    return
  }

  modalLoading.value = true

  try {
    if (editingKey.value) {
      if (modalType.value === 'equipment') {
        await facilitiesApi.updateEquipment(editingKey.value, {
          name: formState.name,
          code: formState.code,
          description: formState.description,
          status: formState.status,
          vendor: formState.vendor,
          model: formState.model,
          equipmentType: formState.equipmentType
        })
        message.success(t('facilities.updateSuccess'))
        modalVisible.value = false
        await loadFacilities()
        return
      }
      // 更新
      if (modalType.value === 'factory') {
        await facilitiesApi.updateFactory(editingKey.value, {
          name: formState.name,
          code: formState.code,
          description: formState.description,
          location: formState.location,
          status: formState.status
        })
      } else if (modalType.value === 'line') {
        await facilitiesApi.updateLine(editingKey.value, {
          name: formState.name,
          code: formState.code,
          description: formState.description,
          status: formState.status
        })
      } else {
        await facilitiesApi.updateStation(editingKey.value, {
          name: formState.name,
          code: formState.code,
          description: formState.description,
          ip: formState.ip,
          mac: formState.mac,
          status: formState.status
        })
      }
      message.success(t('facilities.updateSuccess'))
    } else {
      // 创建
      if (modalType.value === 'factory') {
        await facilitiesApi.createFactory({
          name: formState.name,
          code: formState.code,
          description: formState.description,
          location: formState.location,
          status: formState.status
        })
      } else if (modalType.value === 'line') {
        if (!parentKey.value) {
          message.error('请选择所属厂区')
          return
        }
        await facilitiesApi.createLine({
          factoryId: parentKey.value,
          name: formState.name,
          code: formState.code,
          description: formState.description,
          status: formState.status
        })
      } else {
        if (modalType.value === 'equipment') {
          if (!parentKey.value) {
            message.error('请选择所属工位')
            return
          }
          await facilitiesApi.createEquipment({
            stationId: parentKey.value,
            name: formState.name,
            code: formState.code,
            description: formState.description,
            status: formState.status,
            vendor: formState.vendor,
            model: formState.model,
            equipmentType: formState.equipmentType
          })
          message.success(t('facilities.createSuccess'))
          modalVisible.value = false
          await loadFacilities()
          return
        }
        if (!parentKey.value) {
          message.error('请选择所属线体')
          return
        }
        await facilitiesApi.createStation({
          lineId: parentKey.value,
          name: formState.name,
          code: formState.code,
          description: formState.description,
          ip: formState.ip,
          mac: formState.mac,
          status: formState.status
        })
      }
      message.success(t('facilities.createSuccess'))
    }

    modalVisible.value = false
    await loadFacilities()
  } catch (error) {
    console.error('操作失败:', error)
  } finally {
    modalLoading.value = false
  }
}

const handleModalCancel = () => {
  modalVisible.value = false
}

// 图标组件
const IconFactory = {
  template: `
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#dbeafe" d="M5 40h38v3H5z" />
      <path fill="#94a3b8" d="M9 18l8 5v-5l8 5v-5l8 5V9h7v31H9z" />
      <path fill="#475569" d="M9 18l8 5v17H9zM25 18l8 5v17h-8z" opacity=".28" />
      <path fill="#2563eb" d="M34 9h6v31h-6z" />
      <path fill="#facc15" d="M13 29h5v5h-5zM22 29h5v5h-5zM31 29h5v5h-5z" />
      <path fill="#0f172a" d="M14 38h6v2h-6zM28 38h6v2h-6z" opacity=".22" />
    </svg>
  `
}

const IconLine = {
  template: `
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#dcfce7" d="M6 31h36v7H6z" />
      <path fill="#16a34a" d="M8 28h32v5H8z" />
      <path fill="#0f766e" d="M12 23h24l4 5H8z" />
      <circle cx="14" cy="35" r="3" fill="#334155" />
      <circle cx="24" cy="35" r="3" fill="#334155" />
      <circle cx="34" cy="35" r="3" fill="#334155" />
      <path fill="#f97316" d="M18 14h12l3 9H15z" />
      <path fill="#fde68a" d="M20 16h8l2 5H18z" />
    </svg>
  `
}

const IconStation = {
  template: `
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#ede9fe" d="M10 15h28v21H10z" />
      <path fill="#7c3aed" d="M13 12h22a3 3 0 0 1 3 3v5H10v-5a3 3 0 0 1 3-3z" />
      <path fill="#a78bfa" d="M14 23h20v9H14z" />
      <path fill="#1e293b" d="M16 34h16v3H16zM12 37h24v3H12z" opacity=".35" />
      <circle cx="17" cy="16" r="1.7" fill="#fef08a" />
      <circle cx="23" cy="16" r="1.7" fill="#bbf7d0" />
      <circle cx="29" cy="16" r="1.7" fill="#fecaca" />
    </svg>
  `
}

const IconEquipment = {
  template: `
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <rect x="13" y="9" width="22" height="30" rx="3" fill="#f59e0b" />
      <rect x="16" y="13" width="16" height="8" rx="1.5" fill="#fef3c7" />
      <path fill="#334155" d="M18 26h12v3H18zM18 32h8v3h-8z" />
      <circle cx="31" cy="33.5" r="2.5" fill="#22c55e" />
      <path fill="#94a3b8" d="M9 15h4v4H9zM9 29h4v4H9zM35 15h4v4h-4zM35 29h4v4h-4z" />
      <path stroke="#64748b" stroke-width="2" d="M11 17h-4M11 31h-4M41 17h-4M41 31h-4" />
    </svg>
  `
}
</script>

<style scoped>
:deep(.facility-tree .ant-tree-treenode) {
  padding: 4px 0;
}

:deep(.facility-tree .ant-tree-node-content-wrapper) {
  width: 100%;
}

.facility-node {
  min-height: 44px;
  padding: 6px 10px;
  border-radius: 6px;
}

.facility-node:hover {
  background: #f8fafc;
}

.facility-node-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  box-shadow: 0 1px 2px rgb(15 23 42 / 0.08), inset 0 0 0 1px rgb(226 232 240);
}

.facility-svg-icon {
  width: 34px;
  height: 34px;
  display: block;
}

.facility-icon-factory {
  box-shadow: 0 1px 2px rgb(37 99 235 / 0.16), inset 0 0 0 1px #bfdbfe;
}

.facility-icon-line {
  box-shadow: 0 1px 2px rgb(22 163 74 / 0.16), inset 0 0 0 1px #bbf7d0;
}

.facility-icon-station {
  box-shadow: 0 1px 2px rgb(124 58 237 / 0.16), inset 0 0 0 1px #ddd6fe;
}

.facility-icon-equipment {
  box-shadow: 0 1px 2px rgb(245 158 11 / 0.16), inset 0 0 0 1px #fde68a;
}
</style>
