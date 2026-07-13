<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ t('deployment.title') }}</h1>
        <p class="text-gray-500 mt-1">管理工位部署配置清单</p>
      </div>
      <a-button type="primary" @click="showUploadModal">
        <template #icon>
          <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </template>
        {{ t('deployment.upload') }}
      </a-button>
    </div>

    <div class="bg-white rounded-xl p-4 shadow-sm">
      <a-input-search v-model:value="filters.search" :placeholder="t('common.search')" size="large" allow-clear
        @search="loadManifests" />
    </div>

    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <a-table :columns="columns" :data-source="manifestsData" :pagination="pagination" :loading="loading"
        @change="handleTableChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-green-100 text-green-600 flex items-center justify-center">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <div class="font-medium text-gray-800">{{ record.name }}</div>
                <div class="text-xs text-gray-500">{{ record.fileName }}</div>
              </div>
            </div>
          </template>

          <template v-else-if="column.key === 'version'">
            <span class="font-mono text-sm">{{ record.version }}</span>
          </template>

          <template v-else-if="column.key === 'size'">
            <span class="text-gray-600">{{ formatFileSize(record.size) }}</span>
          </template>

          <template v-else-if="column.key === 'boundStations'">
            <div v-if="record.boundStations && record.boundStations.length > 0">
              <a-tag v-for="station in record.boundStations.slice(0, 2)" :key="station.id" size="small">
                {{ station.name }}
              </a-tag>
              <a-tag v-if="record.boundStations.length > 2" size="small">
                +{{ record.boundStations.length - 2 }}
              </a-tag>
            </div>
            <span v-else class="text-gray-400">未绑定</span>
          </template>

          <template v-else-if="column.key === 'actions'">
            <div class="flex gap-2">
              <a-button size="small" type="link" @click="handleDownload(record.id, record.fileName)">
                {{ t('common.download') }}
              </a-button>
              <a-button size="small" type="link" @click="handleEdit(record)">
                {{ t('common.edit') }}
              </a-button>
              <a-button size="small" type="link" danger @click="handleDelete(record.id)">
                {{ t('common.delete') }}
              </a-button>
            </div>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal v-model:open="uploadModalVisible" :title="t('deployment.upload')" @ok="handleUploadOk"
      @cancel="handleUploadCancel" :confirmLoading="uploading" width="600px">
      <a-form :model="uploadForm" layout="vertical" class="mt-4">
        <a-form-item label="清单名称" name="name" :rules="[{ required: true }]">
          <a-input v-model:value="uploadForm.name" />
        </a-form-item>
        <a-form-item label="版本号" name="version">
          <a-input v-model:value="uploadForm.version" placeholder="例如: 1.0.0" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="uploadForm.description" :rows="3" />
        </a-form-item>
        <a-form-item label="上传文件" name="file">
          <a-upload-dragger v-model:fileList="fileList" :before-upload="beforeUpload" :max-count="1" accept=".toml">
            <p class="ant-upload-drag-icon">
              <svg class="w-12 h-12 mx-auto text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </p>
            <p class="ant-upload-text">{{ t('deployment.dragText') }}</p>
            <p class="ant-upload-hint">{{ t('deployment.dragHint') }}</p>
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
import * as deploymentApi from '../api/deployment'
import type { DeploymentManifest } from '../api/deployment'

const { t } = useI18n()

const loading = ref(false)
const uploadModalVisible = ref(false)
const uploading = ref(false)
const fileList = ref<any[]>([])
const manifestsData = ref<DeploymentManifest[]>([])

const filters = reactive({
  search: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const uploadForm = reactive({
  name: '',
  version: '',
  description: ''
})

const columns = [
  { title: '清单名称', key: 'name', width: 300 },
  { title: '版本', key: 'version', width: 100 },
  { title: '文件大小', key: 'size', width: 120 },
  { title: '绑定工位', key: 'boundStations', width: 200 },
  { title: '上传时间', dataIndex: 'uploadTime', width: 180 },
  { title: '操作', key: 'actions', fixed: 'right', width: 200 }
]

const loadManifests = async () => {
  loading.value = true
  try {
    const response = await deploymentApi.getDeploymentManifests({
      page: pagination.current,
      pageSize: pagination.pageSize,
      search: filters.search
    })
    manifestsData.value = response.data.list
    pagination.total = response.data.total
  } catch (error) {
    console.error('加载清单列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleTableChange: TableProps['onChange'] = (pag) => {
  pagination.current = pag.current || 1
  pagination.pageSize = pag.pageSize || 10
  loadManifests()
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const showUploadModal = () => {
  uploadForm.name = ''
  uploadForm.version = ''
  uploadForm.description = ''
  fileList.value = []
  uploadModalVisible.value = true
}

const beforeUpload: UploadProps['beforeUpload'] = () => {
  return false
}

const handleUploadOk = async () => {
  if (!uploadForm.name || fileList.value.length === 0) {
    message.error('请填写清单名称并上传文件')
    return
  }

  uploading.value = true
  try {
    await deploymentApi.uploadDeploymentManifest({
      file: fileList.value[0].originFileObj,
      name: uploadForm.name,
      version: uploadForm.version,
      description: uploadForm.description
    })
    message.success('上传成功')
    uploadModalVisible.value = false
    await loadManifests()
  } catch (error) {
    console.error('上传失败:', error)
  } finally {
    uploading.value = false
  }
}

const handleUploadCancel = () => {
  uploadModalVisible.value = false
}

const handleEdit = (_record: DeploymentManifest) => {
  // TODO: 实现编辑功能
  message.info('编辑功能开发中')
}

const handleDelete = async (id: string) => {
  Modal.confirm({
    title: '确认删除',
    content: '确认删除此部署清单吗？',
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    okType: 'danger',
    onOk: async () => {
      try {
        await deploymentApi.deleteDeploymentManifest(id)
        message.success('删除成功')
        await loadManifests()
      } catch (error) {
        console.error('删除失败:', error)
      }
    }
  })
}

const handleDownload = async (id: string, fileName: string) => {
  try {
    const response = await deploymentApi.downloadDeploymentManifest(id)
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

onMounted(() => {
  loadManifests()
})
</script>
