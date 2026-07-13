<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ t('interfaces.title') }}</h1>
        <p class="text-gray-500 mt-1">上传和管理界面编辑器导出的界面配置文件</p>
      </div>
      <div class="flex gap-3">
        <a-button @click="handleCreateNewPage">
          <template #icon>
            <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </template>
          新建页面
        </a-button>
        <a-button type="primary" @click="showUploadModal">
          <template #icon>
            <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </template>
          {{ t('common.upload') }}
        </a-button>
      </div>
    </div>

    <div class="bg-white rounded-xl p-4 shadow-sm">
      <a-input-search v-model:value="filters.search" :placeholder="t('common.search')" size="large" allow-clear
        @search="loadInterfaces" />
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center items-center py-20">
      <a-spin size="large" />
    </div>

    <!-- 卡片列表 -->
    <div v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div v-for="item in interfacesData" :key="item.id"
          class="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden border border-gray-100">
          <!-- 卡片头部 -->
          <div class="p-4 bg-gradient-to-br from-blue-50 to-indigo-50">
            <div class="flex items-center justify-center h-32">
              <div class="w-20 h-20 rounded-2xl bg-white shadow-lg flex items-center justify-center">
                <svg class="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </div>

          <!-- 卡片内容 -->
          <div class="p-4">
            <h3 class="font-semibold text-gray-900 text-lg mb-1 truncate" :title="item.name">
              {{ item.name }}
            </h3>
            <p class="text-sm text-gray-500 mb-3 line-clamp-2 h-10" :title="item.description">
              {{ item.description || '暂无描述' }}
            </p>

            <!-- 信息行 -->
            <div class="space-y-2 mb-4">
              <div class="flex items-center text-xs text-gray-600">
                <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <span>{{ formatFileSize(item.fileSize) }}</span>
              </div>

              <div class="flex items-center text-xs text-gray-600">
                <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{{ item.createTime }}</span>
              </div>

              <div class="flex items-start text-xs">
                <svg class="w-4 h-4 mr-1.5 mt-0.5 text-gray-600 flex-shrink-0" fill="none" stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <div class="flex-1">
                  <div v-if="item.boundStations && item.boundStations.length > 0" class="flex flex-wrap gap-1">
                    <a-tag v-for="station in item.boundStations.slice(0, 2)" :key="station.id" size="small"
                      class="text-xs">
                      {{ station.name }}
                    </a-tag>
                    <a-tag v-if="item.boundStations.length > 2" size="small" class="text-xs">
                      +{{ item.boundStations.length - 2 }}
                    </a-tag>
                  </div>
                  <span v-else class="text-gray-400">未绑定工位</span>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex flex-wrap gap-2 pt-3 border-t border-gray-100">
              <a-button size="small" @click="handleDownload(item.id, item.name)" class="flex-1">
                <template #icon>
                  <svg class="w-3.5 h-3.5 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </template>
                {{ t('common.download') }}
              </a-button>
              <a-button size="small" @click="handleEdit(item)" class="flex-1">
                <template #icon>
                  <svg class="w-3.5 h-3.5 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </template>
                {{ t('interfaces.editInfo') }}
              </a-button>
              <a-button size="small" type="primary" @click="handleEditInterface" class="flex-1">
                <template #icon>
                  <svg class="w-3.5 h-3.5 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </template>
                {{ t('interfaces.editInterface') }}
              </a-button>
              <a-button size="small" danger @click="handleDelete(item.id)">
                <template #icon>
                  <svg class="w-3.5 h-3.5 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </template>
                {{ t('common.delete') }}
              </a-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="interfacesData.length === 0" class="bg-white rounded-xl shadow-sm p-12 text-center">
        <div class="w-24 h-24 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
          <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">暂无界面</h3>
        <p class="text-gray-500 mb-6">还没有上传任何界面配置文件</p>
        <a-button type="primary" @click="showUploadModal">
          <template #icon>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </template>
          上传界面
        </a-button>
      </div>

      <!-- 分页 -->
      <div v-if="interfacesData.length > 0" class="mt-6 flex justify-center">
        <a-pagination v-model:current="pagination.current" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :show-size-changer="true" :show-total="(total: number) => `共 ${total} 条`"
          @change="handlePaginationChange" />
      </div>
    </div>

    <!-- 上传对话框 -->
    <a-modal v-model:open="uploadModalVisible" :title="t('common.upload')" @ok="handleUploadOk"
      @cancel="handleUploadCancel" :confirmLoading="uploading" width="600px">
      <a-form :model="uploadForm" layout="vertical" class="mt-4">
        <a-form-item label="界面名称" name="name" :rules="[{ required: true, message: '请输入界面名称' }]">
          <a-input v-model:value="uploadForm.name" placeholder="请输入界面名称" />
        </a-form-item>

        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="uploadForm.description" placeholder="界面描述（可选）" :rows="3" />
        </a-form-item>

        <a-form-item label="上传JSON文件" name="file" :rules="[{ required: true, message: '请上传JSON配置文件' }]">
          <a-upload-dragger v-model:fileList="fileList" :before-upload="beforeUpload" :max-count="1" accept=".json">
            <p class="ant-upload-drag-icon">
              <svg class="w-12 h-12 mx-auto text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">支持上传界面编辑器导出的 .json 配置文件</p>
          </a-upload-dragger>
        </a-form-item>

        <a-form-item label="绑定工位" name="stationIds">
          <a-select v-model:value="uploadForm.stationIds" mode="multiple" placeholder="搜索并选择工位（可选）" show-search
            :filter-option="false" @search="handleStationSearch"
            :not-found-content="stationSearching ? undefined : null" allowClear>
            <template v-if="stationSearching" #notFoundContent>
              <a-spin size="small" />
            </template>
            <a-select-option v-for="station in stationOptions" :key="station.id" :value="station.id">
              <div class="flex flex-col">
                <span class="font-medium">{{ station.name }}</span>
                <span class="text-xs text-gray-500">{{ station.path }}</span>
              </div>
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 编辑对话框 -->
    <a-modal v-model:open="editModalVisible" title="编辑界面信息" @ok="handleEditOk" @cancel="handleEditCancel"
      :confirmLoading="editLoading" width="600px">
      <a-form :model="editForm" layout="vertical" class="mt-4">
        <a-form-item label="界面名称" name="name" :rules="[{ required: true }]">
          <a-input v-model:value="editForm.name" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="editForm.description" :rows="3" />
        </a-form-item>

        <a-form-item label="绑定工位" name="stationIds">
          <a-select v-model:value="editForm.stationIds" mode="multiple" placeholder="搜索并选择工位" show-search
            :filter-option="false" @search="handleStationSearch"
            :not-found-content="stationSearching ? undefined : null" allowClear>
            <template v-if="stationSearching" #notFoundContent>
              <a-spin size="small" />
            </template>
            <a-select-option v-for="station in stationOptions" :key="station.id" :value="station.id">
              <div class="flex flex-col">
                <span class="font-medium">{{ station.name }}</span>
                <span class="text-xs text-gray-500">{{ station.path }}</span>
              </div>
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import type { UploadProps } from 'ant-design-vue'
import * as interfacesApi from '../api/interfaces'
import type { InterfaceInfo } from '../api/interfaces'
import * as facilitiesApi from '../api/facilities'
import type { StationSearchResult } from '../api/facilities'

const { t } = useI18n()

const loading = ref(false)
const uploadModalVisible = ref(false)
const editModalVisible = ref(false)
const uploading = ref(false)
const editLoading = ref(false)
const editingId = ref<string | null>(null)
const fileList = ref<any[]>([])
const interfacesData = ref<InterfaceInfo[]>([])

// 工位搜索相关
const stationSearching = ref(false)
const stationOptions = ref<StationSearchResult[]>([])

const filters = reactive({
  search: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 12,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const uploadForm = reactive({
  name: '',
  description: '',
  stationIds: [] as string[]
})

const editForm = reactive({
  name: '',
  description: '',
  stationIds: [] as string[]
})

const loadInterfaces = async () => {
  loading.value = true
  try {
    const response: any = await interfacesApi.getInterfaces({
      page: pagination.current,
      pageSize: pagination.pageSize,
      search: filters.search
    })
    interfacesData.value = response.data.list
    pagination.total = response.data.total
  } catch (error) {
    console.error('加载界面列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handlePaginationChange = (page: number, pageSize: number) => {
  pagination.current = page
  pagination.pageSize = pageSize
  loadInterfaces()
}

const formatFileSize = (bytes?: number) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const showUploadModal = () => {
  uploadForm.name = ''
  uploadForm.description = ''
  uploadForm.stationIds = []
  fileList.value = []
  stationOptions.value = []
  uploadModalVisible.value = true
}

const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  // 验证文件类型
  if (!file.name.toLowerCase().endsWith('.json')) {
    message.error('只能上传 JSON 格式文件')
    return false
  }
  return false
}

const handleUploadOk = async () => {
  if (!uploadForm.name) {
    message.error('请填写界面名称')
    return
  }

  if (fileList.value.length === 0) {
    message.error('请上传JSON配置文件')
    return
  }

  uploading.value = true
  try {
    await interfacesApi.uploadInterface({
      file: fileList.value[0].originFileObj,
      name: uploadForm.name,
      description: uploadForm.description,
      stationIds: uploadForm.stationIds.length > 0 ? uploadForm.stationIds : undefined
    })
    message.success('上传成功')
    uploadModalVisible.value = false
    await loadInterfaces()
  } catch (error) {
    console.error('上传失败:', error)
  } finally {
    uploading.value = false
  }
}

const handleUploadCancel = () => {
  uploadModalVisible.value = false
}

const handleEdit = (record: InterfaceInfo) => {
  editingId.value = record.id
  editForm.name = record.name
  editForm.description = record.description || ''
  editForm.stationIds = record.boundStations.map(s => s.id)

  // 将当前绑定的工位加入选项列表
  stationOptions.value = record.boundStations.map(station => ({
    id: station.id,
    name: station.name,
    code: station.code,
    path: station.path,
    status: 'active' as const,
    factoryId: '',
    factoryName: '',
    lineId: '',
    lineName: '',
    createTime: '',
    updateTime: ''
  }))

  editModalVisible.value = true
}

const handleEditOk = async () => {
  if (!editForm.name) {
    message.error('请填写界面名称')
    return
  }

  if (!editingId.value) return

  editLoading.value = true
  try {
    await interfacesApi.updateInterfaceInfo(editingId.value, {
      name: editForm.name,
      description: editForm.description,
      stationIds: editForm.stationIds
    })
    message.success('更新成功')
    editModalVisible.value = false
    await loadInterfaces()
  } catch (error) {
    console.error('更新失败:', error)
  } finally {
    editLoading.value = false
  }
}

const handleEditCancel = () => {
  editModalVisible.value = false
}

const handleDelete = async (id: string) => {
  Modal.confirm({
    title: '确认删除',
    content: '确认删除此界面吗？',
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    okType: 'danger',
    onOk: async () => {
      try {
        await interfacesApi.deleteInterface(id)
        message.success('删除成功')
        await loadInterfaces()
      } catch (error) {
        console.error('删除失败:', error)
      }
    }
  })
}

const handleDownload = async (id: string, _name: string) => {
  try {
    // downloadInterfaceJson 已经内置了文件下载逻辑，包括中文文件名支持
    await interfacesApi.downloadInterfaceJson(id)
    message.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

const handleEditInterface = () => {
  window.open('http://localhost:5174/', '_blank')
}

const handleCreateNewPage = () => {
  window.open('http://localhost:5174/', '_blank')
}

// 工位搜索
let searchTimer: ReturnType<typeof setTimeout> | null = null
const handleStationSearch = async (keyword: string) => {
  // 清除之前的定时器
  if (searchTimer) {
    clearTimeout(searchTimer)
  }

  // 如果关键词为空,清空选项
  if (!keyword) {
    stationOptions.value = []
    return
  }

  // 防抖: 延迟300ms后执行搜索
  searchTimer = setTimeout(async () => {
    stationSearching.value = true
    try {
      const response: any = await facilitiesApi.searchStations({
        keyword,
        page: 1,
        pageSize: 20
      })
      stationOptions.value = response.data.list
    } catch (error) {
      console.error('搜索工位失败:', error)
    } finally {
      stationSearching.value = false
    }
  }, 300)
}

onMounted(() => {
  loadInterfaces()
})
</script>
