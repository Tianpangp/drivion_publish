<template>
  <div class="space-y-6">
    <!-- 页面标题和操作 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ t('facilities.title') }}</h1>
        <p class="text-gray-500 mt-1">管理厂区、线体和工位的层级结构</p>
      </div>
      <div class="flex gap-3">
        <a-button @click="showCreateModal('factory')">
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
            <div class="flex items-center justify-between group py-1">
              <div class="flex items-center gap-3">
                <span class="w-8 h-8 rounded-lg flex items-center justify-center" :class="getTypeColor(type)">
                  <component :is="getTypeIcon(type)" class="w-5 h-5" />
                </span>
                <div>
                  <div class="font-medium text-gray-800">{{ title }}</div>
                  <div class="text-xs text-gray-500">{{ getTypeLabel(type) }}</div>
                </div>
              </div>
              <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <a-button v-if="type === 'factory'" size="small" type="link" @click.stop="showCreateModal('line', key)">
                  添加线体
                </a-button>
                <a-button v-if="type === 'line'" size="small" type="link" @click.stop="showCreateModal('station', key)">
                  添加工位
                </a-button>
                <a-button size="small" type="link" @click.stop="handleEdit(key, type)">
                  {{ t('common.edit') }}
                </a-button>
                <a-button size="small" type="link" danger @click.stop="handleDelete(key, type)">
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

        <a-form-item v-if="modalType === 'station'" :label="t('facilities.stationCode')" name="code">
          <a-input v-model:value="formState.code" placeholder="工位编号（可选）" />
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

const { t } = useI18n()

interface FacilityNode {
  key: string
  title: string
  type: FacilityType
  description?: string
  code?: string
  location?: string
  ip?: string
  mac?: string
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
      expandedKeys.value = [treeData.value[0].key]
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
    return t('facilities.editStation')
  }
  if (modalType.value === 'factory') return t('facilities.createFactory')
  if (modalType.value === 'line') return t('facilities.createLine')
  return t('facilities.createStation')
})

const onExpand: TreeProps['onExpand'] = (keys) => {
  expandedKeys.value = keys as string[]
}

const getTypeColor = (type: string) => {
  if (type === 'factory') return 'bg-blue-100 text-blue-600'
  if (type === 'line') return 'bg-green-100 text-green-600'
  return 'bg-purple-100 text-purple-600'
}

const getTypeLabel = (type: string) => {
  if (type === 'factory') return t('facilities.factory')
  if (type === 'line') return t('facilities.line')
  return t('facilities.station')
}

const getTypeIcon = (type: string) => {
  if (type === 'factory') return IconFactory
  if (type === 'line') return IconLine
  return IconStation
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
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  `
}

const IconLine = {
  template: `
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7h16M4 12h16M4 17h16" />
    </svg>
  `
}

const IconStation = {
  template: `
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
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
</style>
