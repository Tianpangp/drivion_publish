<template>
  <div class="space-y-6">
    <!-- 页面标题和操作 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ t('autounit.title') }}</h1>
        <p class="text-gray-500 mt-1">上传、审批和管理设备执行逻辑包，AutoUnit 最终绑定到具体设备</p>
      </div>
      <a-button v-if="canUpload" type="primary" @click="showUploadModal()">
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
          <a-select-option value="pending_testing">{{ t('autounit.pending_testing') }}</a-select-option>
          <a-select-option value="testing">{{ t('autounit.testing') }}</a-select-option>
          <a-select-option value="pending_publish">{{ t('autounit.pending_publish') }}</a-select-option>
          <a-select-option value="removed">{{ t('autounit.removed') }}</a-select-option>
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
            <div class="text-xs text-gray-500 mb-2">绑定设备</div>
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
            <a-button v-if="canSubmitTest && pkg.status === 'pending_testing'" size="small" type="primary"
              @click="handleSubmitTesting(pkg.id)">
              提交测试
            </a-button>
            <a-button v-if="canUpdate && pkg.status === 'pending_testing'" size="small" @click="showUploadModal(pkg.id)">更新</a-button>
            <a-button v-if="canDelete && pkg.status === 'pending_testing'" size="small" danger @click="handleDelete(pkg.id)">删除</a-button>
            <a-button v-if="canSubmitPublish && (pkg.status === 'testing' || pkg.status === 'removed')" size="small" type="primary"
              @click="handleSubmitPublish(pkg.id)">
              {{ pkg.status === 'removed' ? '重新上架' : '提交发布' }}
            </a-button>
            <a-button size="small" @click="handleDownload(pkg.id, pkg.fileName)">
              {{ t('common.download') }}
            </a-button>
            <a-button v-if="canSubmitRemove && pkg.status === 'published'" size="small" danger @click="handleSubmitRemove(pkg.id)">
              申请下架
            </a-button>
            <a-button v-if="canReject(pkg.status)" size="small" danger @click="handleReject(pkg.id)">
              退回待测试
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
    <a-modal v-model:open="uploadModalVisible" :title="updatingId ? '更新 AutoUnit 包' : t('autounit.upload')" @ok="handleUploadOk"
      @cancel="handleUploadCancel" :confirmLoading="uploading" width="600px">
      <a-form layout="vertical" class="mt-4">
        <a-form-item :label="t('common.upload')" name="file">
          <a-upload-dragger v-model:fileList="fileList" :before-upload="beforeUpload" :max-count="1"
            accept=".zip,.tar,.tar.gz,.tgz">
            <p class="ant-upload-drag-icon">
              <svg class="w-12 h-12 mx-auto text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </p>
            <p class="ant-upload-text">{{ t('autounit.dragText') }}</p>
            <p class="ant-upload-hint">最大 100MB；包内必须包含 drivion.project.json，名称和版本由后端自动识别。</p>
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
import * as autounitApi from '../api/autounit'
import type { AutoUnitPackage, AutoUnitStatus } from '../api/autounit'
import { useUserStore } from '../stores/user'

const { t } = useI18n()
const userStore = useUserStore()
const canManage = computed(() => userStore.hasPermission('autounit:manage_draft'))
const canUpload = computed(() => canManage.value || userStore.hasPermission('autounit:upload'))
const canUpdate = computed(() => canManage.value || userStore.hasPermission('autounit:update'))
const canDelete = computed(() => canManage.value || userStore.hasPermission('autounit:delete'))
const canSubmitTest = computed(() => userStore.hasPermission('autounit:submit_test'))
const canSubmitPublish = computed(() => userStore.hasPermission('autounit:submit_publish'))
const canSubmitRemove = computed(() => userStore.hasPermission('autounit:submit_remove'))

const loading = ref(false)
const uploadModalVisible = ref(false)
const uploading = ref(false)
const updatingId = ref<string | null>(null)
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
  if (status === 'pending_testing' || status === 'pending_publish' || status === 'pending_remove') return 'warning'
  if (status === 'removed') return 'default'
  return 'warning'
}

const canReject = (status: string) => {
  return canUpdate.value && ['testing', 'pending_publish'].includes(status)
}

const getStatusName = (status: string) => {
  return t(`autounit.${status}`)
}

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

const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  const maxSize = 100 * 1024 * 1024
  if (file.size > maxSize) {
    message.error('AutoUnit 包不能超过 100MB')
    return false
  }
  return false
}

const handleUploadOk = async () => {
  if (fileList.value.length === 0) {
    message.error('请上传 AutoUnit 包')
    return
  }

  uploading.value = true

  try {
    const file = fileList.value[0].originFileObj
    if (updatingId.value) await autounitApi.replaceAutoUnitPackage(updatingId.value, file)
    else await autounitApi.uploadAutoUnitPackage({ file })

    message.success(updatingId.value ? '更新成功' : '上传成功')
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

const handleSubmitTesting = async (id: string) => {
  Modal.confirm({
    title: '提交测试',
    content: '审批通过后转为已测试。',
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    onOk: async () => {
      try {
        await autounitApi.submitAutoUnitTesting(id)
        message.success('已提交测试审批')
        await loadPackages()
      } catch (error) {
        console.error('提交测试失败:', error)
      }
    }
  })
}

const handleSubmitPublish = async (id: string) => {
  Modal.confirm({
    title: '提交发布',
    content: '提交后进入待发布状态，审批通过后转为已发布。',
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    onOk: async () => {
      try {
        await autounitApi.submitAutoUnitPublish(id)
        message.success('已提交发布')
        await loadPackages()
      } catch (error) {
        console.error('提交发布失败:', error)
      }
    }
  })
}

const handleReject = async (id: string) => {
  Modal.confirm({
    title: '退回待测试',
    content: '该版本将回到待测试，可重新更新、提交测试或删除。',
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    okType: 'danger',
    onOk: async () => {
      try {
        await autounitApi.rejectAutoUnitPackage(id)
        message.success('已退回待测试')
        await loadPackages()
      } catch (error) {
        console.error('驳回失败:', error)
      }
    }
  })
}

const handleDelete = (id: string) => {
  Modal.confirm({
    title: '删除待测试版本', content: '记录和已上传的包文件都会直接删除，此操作不可恢复。', okType: 'danger',
    onOk: async () => {
      await autounitApi.deleteAutoUnitPackage(id)
      message.success('已删除')
      await loadPackages()
    }
  })
}

const handleSubmitRemove = async (id: string) => {
  Modal.confirm({
    title: '申请下架',
    content: '下架需要审批，通过后该版本不再允许新绑定和新拉取。',
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    okType: 'danger',
    onOk: async () => {
      try {
        await autounitApi.submitAutoUnitRemove(id)
        message.success('已提交下架审批')
        await loadPackages()
      } catch (error) {
        console.error('提交下架失败:', error)
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
