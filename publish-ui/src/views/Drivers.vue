<template>
  <div class="space-y-6">
    <!-- 页面标题和操作 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ t('drivers.title') }}</h1>
        <p class="text-gray-500 mt-1">上传和管理 Java、Python、C++ 驱动包</p>
      </div>
      <a-button type="primary" @click="showUploadModal">
        <template #icon>
          <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </template>
        {{ t('drivers.upload') }}
      </a-button>
    </div>

    <!-- 筛选器 -->
    <div class="bg-white rounded-xl p-4 shadow-sm">
      <div class="flex gap-4">
        <a-select v-model:value="filters.type" :placeholder="t('drivers.selectType')" class="w-48" allow-clear
          @change="loadDrivers">
          <a-select-option value="java">{{ t('drivers.java') }}</a-select-option>
          <a-select-option value="python">{{ t('drivers.python') }}</a-select-option>
          <a-select-option value="cpp">{{ t('drivers.cpp') }}</a-select-option>
        </a-select>

        <a-select v-model:value="filters.status" placeholder="发布状态" class="w-48" allow-clear @change="loadDrivers">
          <a-select-option value="published">{{ t('drivers.published') }}</a-select-option>
          <a-select-option value="unpublished">{{ t('drivers.unpublished') }}</a-select-option>
          <a-select-option value="testing">{{ t('drivers.testing') }}</a-select-option>
        </a-select>

        <a-input-search v-model:value="filters.search" :placeholder="t('common.search')" class="flex-1" allow-clear
          @search="loadDrivers" />
      </div>
    </div>

    <!-- 驱动包列表 -->
    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <a-table :columns="columns" :data-source="driversData" :pagination="pagination" :loading="loading"
        @change="handleTableChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="getTypeColor(record.type)">
                <component :is="getTypeIcon(record.type)" class="w-5 h-5" />
              </div>
              <div>
                <div class="font-medium text-gray-800">{{ record.name }}</div>
                <div class="text-xs text-gray-500">{{ record.fileName }}</div>
              </div>
            </div>
          </template>

          <template v-else-if="column.key === 'type'">
            <a-tag :color="getDriverTypeColor(record.type)">
              {{ getDriverTypeName(record.type) }}
            </a-tag>
          </template>

          <template v-else-if="column.key === 'version'">
            <span class="font-mono text-sm">{{ record.version }}</span>
          </template>

          <template v-else-if="column.key === 'size'">
            <span class="text-gray-600">{{ formatFileSize(record.size) }}</span>
          </template>

          <template v-else-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusName(record.status) }}
            </a-tag>
          </template>

          <template v-else-if="column.key === 'uploadTime'">
            <span class="text-gray-600 text-sm">{{ record.uploadTime }}</span>
          </template>

          <template v-else-if="column.key === 'actions'">
            <div class="flex gap-2">
              <a-button v-if="record.status === 'unpublished' || record.status === 'testing'" size="small" type="link"
                @click="handlePublish(record.id)">
                {{ t('drivers.publish') }}
              </a-button>
              <a-button size="small" type="link" @click="handleDownload(record.id, record.fileName)">
                {{ t('common.download') }}
              </a-button>
              <a-button v-if="record.status === 'published'" size="small" type="link" danger
                @click="handleUnpublish(record.id)">
                {{ t('drivers.unpublish') }}
              </a-button>
              <a-button v-if="record.status === 'unpublished' || record.status === 'testing'" size="small" type="link"
                danger @click="handleRecall(record.id)">
                {{ t('drivers.recall') }}
              </a-button>
            </div>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 上传对话框 -->
    <a-modal v-model:open="uploadModalVisible" :title="t('drivers.upload')" @ok="handleUploadOk"
      @cancel="handleUploadCancel" :confirmLoading="uploading" width="600px">
      <a-form :model="uploadForm" layout="vertical" class="mt-4">
        <a-form-item :label="t('drivers.driverType')" name="type" :rules="[{ required: true, message: '请选择驱动类型' }]">
          <a-select v-model:value="uploadForm.type" :placeholder="t('drivers.selectType')">
            <a-select-option value="java">
              <div class="flex items-center gap-2">
                <span>☕</span>
                {{ t('drivers.java') }}
              </div>
            </a-select-option>
            <a-select-option value="python">
              <div class="flex items-center gap-2">
                <span>🐍</span>
                {{ t('drivers.python') }}
              </div>
            </a-select-option>
            <a-select-option value="cpp">
              <div class="flex items-center gap-2">
                <span>⚙️</span>
                {{ t('drivers.cpp') }}
              </div>
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item :label="t('common.name')" name="name" :rules="[{ required: true, message: '请输入驱动名称' }]">
          <a-input v-model:value="uploadForm.name" placeholder="请输入驱动名称" />
        </a-form-item>

        <a-form-item :label="t('common.version')" name="version" :rules="[{ required: true, message: '请输入版本号' }]">
          <a-input v-model:value="uploadForm.version" placeholder="例如: 1.0.0" />
        </a-form-item>

        <a-form-item :label="t('common.description')" name="description">
          <a-textarea v-model:value="uploadForm.description" :placeholder="t('common.description')" :rows="3" />
        </a-form-item>

        <a-form-item :label="t('common.upload')" name="file">
          <a-upload-dragger v-model:fileList="fileList" :before-upload="beforeUpload" :max-count="1"
            accept=".zip,.tar.gz,.dll,.so">
            <p class="ant-upload-drag-icon">
              <svg class="w-12 h-12 mx-auto text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </p>
            <p class="ant-upload-text">{{ t('drivers.dragText') }}</p>
            <p class="ant-upload-hint">{{ t('drivers.dragHint') }}</p>
          </a-upload-dragger>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import type { UploadProps, TableProps } from 'ant-design-vue'
import * as driversApi from '../api/drivers'
import type { DriverPackage, DriverType, DriverStatus } from '../api/drivers'

const { t } = useI18n()

const loading = ref(false)
const uploadModalVisible = ref(false)
const uploading = ref(false)
const fileList = ref<any[]>([])
const driversData = ref<DriverPackage[]>([])

const filters = reactive({
  search: '',
  type: undefined as DriverType | undefined,
  status: undefined as DriverStatus | undefined
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const uploadForm = reactive({
  type: undefined as DriverType | undefined,
  name: '',
  version: '',
  description: '',
  protocol: '',
  manufacturer: '',
  deviceModel: ''
})

const columns = [
  {
    title: t('common.name'),
    dataIndex: 'name',
    key: 'name',
    width: 300
  },
  {
    title: t('drivers.driverType'),
    dataIndex: 'type',
    key: 'type',
    width: 120
  },
  {
    title: t('common.version'),
    dataIndex: 'version',
    key: 'version',
    width: 100
  },
  {
    title: '文件大小',
    dataIndex: 'size',
    key: 'size',
    width: 120
  },
  {
    title: t('common.status'),
    key: 'status',
    width: 100
  },
  {
    title: t('drivers.uploadTime'),
    dataIndex: 'uploadTime',
    key: 'uploadTime',
    width: 180
  },
  {
    title: t('common.actions'),
    key: 'actions',
    fixed: 'right',
    width: 250
  }
]

// 加载驱动包列表
const loadDrivers = async () => {
  loading.value = true
  try {
    const response = await driversApi.getDriverPackages({
      page: pagination.current,
      pageSize: pagination.pageSize,
      search: filters.search,
      type: filters.type,
      status: filters.status
    })

    driversData.value = response.data.list
    pagination.total = response.data.total
  } catch (error) {
    console.error('加载驱动包列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 表格变化处理
const handleTableChange: TableProps['onChange'] = (pag) => {
  pagination.current = pag.current || 1
  pagination.pageSize = pag.pageSize || 10
  loadDrivers()
}

const getTypeColor = (type: string) => {
  if (type === 'java') return 'bg-orange-100 text-orange-600'
  if (type === 'python') return 'bg-blue-100 text-blue-600'
  return 'bg-purple-100 text-purple-600'
}

const getTypeIcon = (type: string) => {
  if (type === 'java') return IconJava
  if (type === 'python') return IconPython
  return IconCpp
}

const getDriverTypeColor = (type: string) => {
  if (type === 'java') return 'orange'
  if (type === 'python') return 'blue'
  return 'purple'
}

const getDriverTypeName = (type: string) => {
  return t(`drivers.${type}`)
}

const getStatusColor = (status: string) => {
  if (status === 'published') return 'success'
  if (status === 'testing') return 'processing'
  return 'default'
}

const getStatusName = (status: string) => {
  return t(`drivers.${status}`)
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const showUploadModal = () => {
  uploadForm.type = undefined
  uploadForm.name = ''
  uploadForm.version = ''
  uploadForm.description = ''
  uploadForm.protocol = ''
  uploadForm.manufacturer = ''
  uploadForm.deviceModel = ''
  fileList.value = []
  uploadModalVisible.value = true
}

const beforeUpload: UploadProps['beforeUpload'] = () => {
  return false
}

const handleUploadOk = async () => {
  if (!uploadForm.type || !uploadForm.name || !uploadForm.version || fileList.value.length === 0) {
    message.error('请填写完整信息并上传文件')
    return
  }

  uploading.value = true

  try {
    await driversApi.uploadDriverPackage({
      file: fileList.value[0].originFileObj,
      type: uploadForm.type,
      name: uploadForm.name,
      version: uploadForm.version,
      description: uploadForm.description,
      protocol: uploadForm.protocol,
      manufacturer: uploadForm.manufacturer,
      deviceModel: uploadForm.deviceModel
    })

    message.success(t('drivers.uploadSuccess'))
    uploadModalVisible.value = false
    await loadDrivers()
  } catch (error) {
    console.error('上传失败:', error)
  } finally {
    uploading.value = false
  }
}

const handleUploadCancel = () => {
  uploadModalVisible.value = false
}

const handlePublish = async (id: string) => {
  Modal.confirm({
    title: '确认发布',
    content: '确认发布此驱动包吗？发布后将可供使用。',
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    onOk: async () => {
      try {
        await driversApi.publishDriverPackage(id)
        message.success(t('drivers.publishSuccess'))
        await loadDrivers()
      } catch (error) {
        console.error('发布失败:', error)
      }
    }
  })
}

const handleUnpublish = async (id: string) => {
  Modal.confirm({
    title: t('drivers.unpublishConfirm'),
    content: '下架后该驱动包将不可使用，但数据会保留。',
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    okType: 'danger',
    onOk: async () => {
      try {
        await driversApi.unpublishDriverPackage(id)
        message.success(t('drivers.unpublishSuccess'))
        await loadDrivers()
      } catch (error) {
        console.error('下架失败:', error)
      }
    }
  })
}

const handleRecall = async (id: string) => {
  Modal.confirm({
    title: t('drivers.recallConfirm'),
    content: '撤回后该驱动包将被删除，此操作不可恢复。',
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    okType: 'danger',
    onOk: async () => {
      try {
        await driversApi.recallDriverPackage(id)
        message.success(t('drivers.recallSuccess'))
        await loadDrivers()
      } catch (error) {
        console.error('撤回失败:', error)
      }
    }
  })
}

const handleDownload = async (id: string, fileName: string) => {
  try {
    const response = await driversApi.downloadDriverPackage(id)

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    message.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadDrivers()
})

// 图标组件
const IconJava = {
  template: `
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M8.851 18.56s-.917.534.653.714c1.902.218 2.874.187 4.969-.211 0 0 .552.346 1.321.646-4.699 2.013-10.633-.118-6.943-1.149M8.276 15.933s-1.028.761.542.924c2.032.209 3.636.227 6.413-.308 0 0 .384.389.987.602-5.679 1.661-12.007.13-7.942-1.218M13.116 11.475c1.158 1.333-.304 2.533-.304 2.533s2.939-1.518 1.589-3.418c-1.261-1.772-2.228-2.652 3.007-5.688 0-.001-8.216 2.051-4.292 6.573M19.33 20.504s.679.559-.747.991c-2.712.822-11.288 1.069-13.669.033-.856-.373.75-.89 1.254-.998.527-.114.828-.093.828-.093-.953-.671-6.156 1.317-2.643 1.887 9.58 1.553 17.462-.7 14.977-1.82M9.292 13.21s-4.362 1.036-1.544 1.412c1.189.159 3.561.123 5.77-.062 1.806-.152 3.618-.477 3.618-.477s-.637.272-1.098.587c-4.429 1.165-12.986.623-10.522-.568 2.082-1.006 3.776-.892 3.776-.892M17.116 17.584c4.503-2.34 2.421-4.589.968-4.285-.355.074-.515.138-.515.138s.132-.207.385-.297c2.875-1.011 5.086 2.981-.928 4.562 0-.001.07-.062.09-.118M14.401 0s2.494 2.494-2.365 6.33c-3.896 3.077-.888 4.832-.001 6.836-2.274-2.053-3.943-3.858-2.824-5.539 1.644-2.469 6.197-3.665 5.19-7.627M9.734 23.924c4.322.277 10.959-.153 11.116-2.198 0 0-.302.775-3.572 1.391-3.688.694-8.239.613-10.937.168 0-.001.553.457 3.393.639"/>
    </svg>
  `
}

const IconPython = {
  template: `
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z"/>
    </svg>
  `
}

const IconCpp = {
  template: `
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M22.394 6c-.167-.29-.398-.543-.652-.69L12.926.22c-.509-.294-1.34-.294-1.848 0L2.26 5.31c-.508.293-.923 1.013-.923 1.6v10.18c0 .294.104.62.271.91.167.29.398.543.652.69l8.816 5.09c.508.293 1.34.293 1.848 0l8.816-5.09c.254-.147.485-.4.652-.69.167-.29.27-.616.27-.91V6.91c.003-.294-.1-.62-.268-.91zM12 19.11c-3.92 0-7.109-3.19-7.109-7.11 0-3.92 3.19-7.11 7.11-7.11a7.133 7.133 0 016.156 3.553l-3.076 1.78a3.567 3.567 0 00-3.08-1.78A3.56 3.56 0 008.444 12 3.56 3.56 0 0012 15.555a3.57 3.57 0 003.08-1.778l3.078 1.78A7.135 7.135 0 0112 19.11zm7.11-6.715h-.79v.79h-.79v-.79h-.79v-.79h.79v-.79h.79v.79h.79v.79zm2.962 0h-.79v.79h-.79v-.79h-.79v-.79h.79v-.79h.79v.79h.79v.79z"/>
    </svg>
  `
}
</script>
