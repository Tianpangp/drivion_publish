<template>
  <div class="space-y-6">
    <!-- 页面标题和操作 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ t('autounit.title') }}</h1>
        <p class="text-gray-500 mt-1">上传和管理 AutoUnit Python 包</p>
      </div>
      <a-button type="primary" @click="showUploadModal">
        <template #icon>
          <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </template>
        {{ t('autounit.upload') }}
      </a-button>
    </div>

    <!-- 搜索和筛选 -->
    <div class="bg-white rounded-xl p-4 shadow-sm">
      <div class="flex gap-4">
        <a-select v-model:value="filters.status" placeholder="发布状态" class="w-48" allow-clear @change="loadPackages">
          <a-select-option value="published">{{ t('autounit.published') }}</a-select-option>
          <a-select-option value="unpublished">{{ t('autounit.unpublished') }}</a-select-option>
          <a-select-option value="testing">{{ t('autounit.testing') }}</a-select-option>
        </a-select>

        <a-input-search v-model:value="filters.search" :placeholder="t('common.search')" size="middle" class="flex-1"
          allow-clear @search="loadPackages" />
      </div>
    </div>

    <!-- AutoUnit 包列表 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="pkg in packagesData" :key="pkg.id"
        class="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden">
        <div class="p-6">
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <div
                class="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <div>
                <h3 class="font-semibold text-gray-800">{{ pkg.name }}</h3>
                <p class="text-sm text-gray-500">v{{ pkg.version }}</p>
              </div>
            </div>
            <a-tag :color="getStatusColor(pkg.status)">
              {{ getStatusName(pkg.status) }}
            </a-tag>
          </div>

          <div class="space-y-2 mb-4">
            <div class="flex items-center text-sm text-gray-600">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              {{ pkg.fileName }}
            </div>
            <div class="flex items-center text-sm text-gray-600">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ pkg.uploadTime }}
            </div>
            <div class="flex items-center text-sm text-gray-600">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
              {{ formatFileSize(pkg.size) }}
            </div>
          </div>

          <div v-if="pkg.description" class="mb-4">
            <p class="text-sm text-gray-600 line-clamp-2">{{ pkg.description }}</p>
          </div>

          <div v-if="pkg.boundStations && pkg.boundStations.length > 0" class="mb-4">
            <div class="text-xs text-gray-500 mb-2">绑定工位</div>
            <div class="flex flex-wrap gap-1">
              <a-tag v-for="station in pkg.boundStations.slice(0, 3)" :key="station.id" size="small">
                {{ station.name }}
              </a-tag>
              <a-tag v-if="pkg.boundStations.length > 3" size="small">
                +{{ pkg.boundStations.length - 3 }}
              </a-tag>
            </div>
          </div>

          <div class="flex gap-2 pt-4 border-t">
            <a-button v-if="pkg.status === 'unpublished' || pkg.status === 'testing'" size="small" type="primary"
              @click="handlePublish(pkg.id)">
              {{ t('autounit.publish') }}
            </a-button>
            <a-button size="small" @click="handleDownload(pkg.id, pkg.fileName)">
              {{ t('common.download') }}
            </a-button>
            <a-button size="small" danger @click="handleRecall(pkg.id)">
              {{ t('autounit.recall') }}
            </a-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="flex justify-center">
      <a-pagination v-model:current="pagination.current" v-model:pageSize="pagination.pageSize"
        :total="pagination.total" :show-total="(total: number) => `共 ${total} 条`" show-size-changer
        @change="loadPackages" />
    </div>

    <!-- 上传对话框 -->
    <a-modal v-model:open="uploadModalVisible" :title="t('autounit.upload')" @ok="handleUploadOk"
      @cancel="handleUploadCancel" :confirmLoading="uploading" width="600px">
      <a-form :model="uploadForm" layout="vertical" class="mt-4">
        <a-form-item :label="t('autounit.packageName')" name="name" :rules="[{ required: true, message: '请输入包名称' }]">
          <a-input v-model:value="uploadForm.name" placeholder="请输入包名称" />
        </a-form-item>

        <a-form-item :label="t('common.version')" name="version" :rules="[{ required: true, message: '请输入版本号' }]">
          <a-input v-model:value="uploadForm.version" placeholder="例如: 1.0.0" />
        </a-form-item>

        <a-form-item :label="t('common.description')" name="description">
          <a-textarea v-model:value="uploadForm.description" :placeholder="t('common.description')" :rows="3" />
        </a-form-item>

        <a-form-item :label="t('common.upload')" name="file">
          <a-upload-dragger v-model:fileList="fileList" :before-upload="beforeUpload" :max-count="1"
            accept=".zip,.tar.gz">
            <p class="ant-upload-drag-icon">
              <svg class="w-12 h-12 mx-auto text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </p>
            <p class="ant-upload-text">{{ t('autounit.dragText') }}</p>
            <p class="ant-upload-hint">{{ t('autounit.dragHint') }}</p>
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
import type { UploadProps } from 'ant-design-vue'
import * as autounitApi from '../api/autounit'
import type { AutoUnitPackage, AutoUnitStatus } from '../api/autounit'

const { t } = useI18n()

const loading = ref(false)
const uploadModalVisible = ref(false)
const uploading = ref(false)
const fileList = ref<any[]>([])
const packagesData = ref<AutoUnitPackage[]>([])

const filters = reactive({
  search: '',
  status: undefined as AutoUnitStatus | undefined
})

const pagination = reactive({
  current: 1,
  pageSize: 12,
  total: 0
})

const uploadForm = reactive({
  name: '',
  version: '',
  description: '',
  pythonVersion: ''
})

// 加载包列表
const loadPackages = async () => {
  loading.value = true
  try {
    const response = await autounitApi.getAutoUnitPackages({
      page: pagination.current,
      pageSize: pagination.pageSize,
      search: filters.search,
      status: filters.status
    })

    packagesData.value = response.data.list
    pagination.total = response.data.total
  } catch (error) {
    console.error('加载包列表失败:', error)
  } finally {
    loading.value = false
  }
}

const getStatusColor = (status: string) => {
  if (status === 'published') return 'success'
  if (status === 'testing') return 'processing'
  return 'default'
}

const getStatusName = (status: string) => {
  return t(`autounit.${status}`)
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
  uploadForm.pythonVersion = ''
  fileList.value = []
  uploadModalVisible.value = true
}

const beforeUpload: UploadProps['beforeUpload'] = () => {
  return false
}

const handleUploadOk = async () => {
  if (!uploadForm.name || !uploadForm.version || fileList.value.length === 0) {
    message.error('请填写完整信息并上传文件')
    return
  }

  uploading.value = true

  try {
    await autounitApi.uploadAutoUnitPackage({
      file: fileList.value[0].originFileObj,
      name: uploadForm.name,
      version: uploadForm.version,
      description: uploadForm.description,
      pythonVersion: uploadForm.pythonVersion
    })

    message.success('上传成功')
    uploadModalVisible.value = false
    await loadPackages()
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
    content: '确认发布此 AutoUnit 包吗？',
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    onOk: async () => {
      try {
        await autounitApi.updateAutoUnitStatus(id, 'published')
        message.success(t('autounit.publishSuccess'))
        await loadPackages()
      } catch (error) {
        console.error('发布失败:', error)
      }
    }
  })
}

const handleRecall = async (id: string) => {
  Modal.confirm({
    title: t('autounit.recallConfirm'),
    content: '撤回后该包将被删除，此操作不可恢复。',
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    okType: 'danger',
    onOk: async () => {
      try {
        await autounitApi.recallAutoUnitPackage(id)
        message.success(t('autounit.recallSuccess'))
        await loadPackages()
      } catch (error) {
        console.error('撤回失败:', error)
      }
    }
  })
}

const handleDownload = async (id: string, fileName: string) => {
  try {
    const response = await autounitApi.downloadAutoUnitPackage(id)

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
  loadPackages()
})
</script>
