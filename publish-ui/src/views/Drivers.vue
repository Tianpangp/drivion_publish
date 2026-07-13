<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ t('drivers.title') }}</h1>
        <p class="text-gray-500 mt-1">上传、审批和管理 HAL 驱动包版本；HAL 由 AutoUnit 在 Exe 中调用</p>
      </div>
      <a-button v-if="canManage" type="primary" @click="showUploadModal()">{{ t('drivers.upload') }}</a-button>
    </div>

    <div class="bg-white rounded-xl p-4 shadow-sm">
      <div class="flex gap-4">
        <a-select v-model:value="filters.status" placeholder="发布状态" class="w-48" allow-clear @change="loadDrivers">
          <a-select-option value="published">{{ t('drivers.published') }}</a-select-option>
          <a-select-option value="pending_testing">{{ t('drivers.pending_testing') }}</a-select-option>
          <a-select-option value="testing">{{ t('drivers.testing') }}</a-select-option>
          <a-select-option value="pending_publish">{{ t('drivers.pending_publish') }}</a-select-option>
          <a-select-option value="pending_remove">{{ t('drivers.pending_remove') }}</a-select-option>
          <a-select-option value="removed">已下架</a-select-option>
        </a-select>
        <a-input-search v-model:value="filters.search" :placeholder="t('common.search')" class="flex-1" allow-clear @search="loadDrivers" />
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="pkg in driversData" :key="pkg.id" class="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden">
        <div class="p-6">
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-12 h-12 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
                <IconPython class="w-7 h-7" />
              </div>
              <div class="min-w-0">
                <h3 class="font-semibold text-gray-800 break-words">{{ pkg.name }}</h3>
                <p class="text-sm text-gray-500">v{{ pkg.version }}</p>
              </div>
            </div>
            <a-tag :color="getStatusColor(pkg.status)">{{ getStatusName(pkg.status) }}</a-tag>
          </div>

          <div class="space-y-2 mb-4">
            <div class="flex items-center text-sm text-gray-600">
              <span class="text-gray-400 mr-2">文件</span>
              <span class="break-all">{{ pkg.fileName }}</span>
            </div>
            <div class="flex items-center text-sm text-gray-600">
              <span class="text-gray-400 mr-2">类型</span>
              <a-tag color="blue">Python</a-tag>
            </div>
            <div class="flex items-center text-sm text-gray-600">
              <span class="text-gray-400 mr-2">上传</span>
              {{ pkg.uploadTime }}
            </div>
            <div class="flex items-center text-sm text-gray-600">
              <span class="text-gray-400 mr-2">大小</span>
              {{ formatFileSize(pkg.size) }}
            </div>
          </div>

          <div v-if="pkg.description" class="mb-4">
            <p class="text-sm text-gray-600 line-clamp-2">{{ pkg.description }}</p>
          </div>

          <div class="flex flex-wrap gap-2 pt-4 border-t">
            <a-button v-if="canSubmitTest && pkg.status === 'pending_testing'" size="small" type="primary" @click="handleSubmitTesting(pkg.id)">提交测试</a-button>
            <a-button v-if="canManage && pkg.status === 'pending_testing'" size="small" @click="showUploadModal(pkg.id)">更新</a-button>
            <a-button v-if="canManage && pkg.status === 'pending_testing'" size="small" danger @click="handleDelete(pkg.id)">删除</a-button>
            <a-button v-if="canSubmitPublish && (pkg.status === 'testing' || pkg.status === 'removed')" size="small" type="primary" @click="handleSubmitPublish(pkg.id)">
              {{ pkg.status === 'removed' ? '重新上架' : '提交发布' }}
            </a-button>
            <a-button size="small" @click="handleDownload(pkg.id, pkg.fileName)">{{ t('common.download') }}</a-button>
            <a-button v-if="canSubmitRemove && pkg.status === 'published'" size="small" danger @click="handleSubmitRemove(pkg.id)">申请下架</a-button>
            <a-button v-if="canReject(pkg.status)" size="small" danger @click="handleReject(pkg.id)">退回待测试</a-button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex justify-center">
      <a-pagination v-model:current="pagination.current" v-model:pageSize="pagination.pageSize"
        :total="pagination.total" :show-total="(total: number) => `共 ${total} 条`" show-size-changer
        @change="loadDrivers" />
    </div>

    <a-modal v-model:open="uploadModalVisible" :title="updatingId ? '更新 HAL 驱动包' : t('drivers.upload')" @ok="handleUploadOk"
      @cancel="handleUploadCancel" :confirmLoading="uploading" width="600px">
      <a-form layout="vertical" class="mt-4">
        <a-form-item :label="t('common.upload')" name="file">
          <a-upload-dragger v-model:fileList="fileList" :before-upload="beforeUpload" :max-count="1"
            accept=".zip,.tar,.tar.gz,.tgz">
            <p class="ant-upload-drag-icon">
              <IconPython class="w-12 h-12 mx-auto text-blue-500" />
            </p>
            <p class="ant-upload-text">{{ t('drivers.dragText') }}</p>
            <p class="ant-upload-hint">当前只支持 Python HAL 包；包内需包含 pyproject.toml，由后端自动识别名称、版本和 entry point。</p>
          </a-upload-dragger>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import type { UploadProps } from 'ant-design-vue'
import * as driversApi from '../api/drivers'
import type { DriverPackage, DriverStatus } from '../api/drivers'
import { useUserStore } from '../stores/user'

const { t } = useI18n()
const userStore = useUserStore()
const canManage = computed(() => userStore.hasPermission('driver:manage_draft'))
const canSubmitTest = computed(() => userStore.hasPermission('driver:submit_test'))
const canSubmitPublish = computed(() => userStore.hasPermission('driver:submit_publish'))
const canSubmitRemove = computed(() => userStore.hasPermission('driver:submit_remove'))

const loading = ref(false)
const uploadModalVisible = ref(false)
const uploading = ref(false)
const updatingId = ref<string | null>(null)
const fileList = ref<any[]>([])
const driversData = ref<DriverPackage[]>([])

const filters = reactive({
  search: '',
  status: undefined as DriverStatus | undefined
})

const pagination = reactive({
  current: 1,
  pageSize: 12,
  total: 0
})

const loadDrivers = async () => {
  loading.value = true
  try {
    const response = await driversApi.getDriverPackages({
      page: pagination.current,
      pageSize: pagination.pageSize,
      search: filters.search,
      status: filters.status
    })
    driversData.value = response.data.list
    pagination.total = response.data.total
  } finally {
    loading.value = false
  }
}

const getStatusColor = (status: string) => {
  if (status === 'published') return 'success'
  if (status === 'testing') return 'processing'
  if (status === 'pending_testing' || status === 'pending_publish' || status === 'pending_remove') return 'warning'
  if (status === 'removed') return 'default'
  return 'warning'
}

const canReject = (status: string) => {
  return canManage.value && ['testing', 'pending_publish'].includes(status)
}

const getStatusName = (status: string) => t(`drivers.${status}`)

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const showUploadModal = (id?: string) => {
  fileList.value = []
  updatingId.value = id || null
  uploadModalVisible.value = true
}

const beforeUpload: UploadProps['beforeUpload'] = () => false

const handleUploadOk = async () => {
  if (fileList.value.length === 0) {
    message.error('请上传 HAL 驱动包')
    return
  }
  uploading.value = true
  try {
    const file = fileList.value[0].originFileObj
    if (updatingId.value) await driversApi.replaceDriverPackage(updatingId.value, file)
    else await driversApi.uploadDriverPackage({ file })
    message.success(updatingId.value ? '更新成功' : t('drivers.uploadSuccess'))
    uploadModalVisible.value = false
    await loadDrivers()
  } finally {
    uploading.value = false
  }
}

const handleUploadCancel = () => {
  uploadModalVisible.value = false
}

const handleSubmitTesting = (id: string) => {
  Modal.confirm({
    title: '提交测试',
    content: '审批通过后转为已测试。',
    onOk: async () => {
      await driversApi.submitDriverTesting(id)
      message.success('已提交测试审批')
      await loadDrivers()
    }
  })
}

const handleSubmitPublish = (id: string) => {
  Modal.confirm({
    title: '提交发布',
    content: '提交后进入待发布状态，审批通过后转为已发布。',
    onOk: async () => {
      await driversApi.submitDriverPublish(id)
      message.success('已提交发布')
      await loadDrivers()
    }
  })
}

const handleSubmitRemove = (id: string) => {
  Modal.confirm({
    title: '申请下架',
    content: '下架需要审批，通过后该版本不再允许新使用。',
    okType: 'danger',
    onOk: async () => {
      await driversApi.submitDriverRemove(id)
      message.success('已提交下架审批')
      await loadDrivers()
    }
  })
}

const handleReject = (id: string) => {
  Modal.confirm({
    title: '退回待测试',
    content: '该版本将回到待测试，可重新更新、提交测试或删除。',
    okType: 'danger',
    onOk: async () => {
      await driversApi.rejectDriverPackage(id)
      message.success('已退回待测试')
      await loadDrivers()
    }
  })
}

const handleDelete = (id: string) => {
  Modal.confirm({
    title: '删除待测试版本', content: '记录和已上传的包文件都会直接删除，此操作不可恢复。', okType: 'danger',
    onOk: async () => {
      await driversApi.deleteDriverPackage(id)
      message.success('已删除')
      await loadDrivers()
    }
  })
}

const handleDownload = async (id: string, fileName: string) => {
  const response = await driversApi.downloadDriverPackage(id)
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', fileName)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
  message.success('下载成功')
}

const IconPython = {
  template: `
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z"/>
    </svg>
  `
}

onMounted(loadDrivers)
</script>
