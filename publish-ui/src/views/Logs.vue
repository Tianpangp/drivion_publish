<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ t('logs.title') }}</h1>
        <p class="text-gray-500 mt-1">查看系统操作日志记录</p>
      </div>
      <a-button @click="handleExport">
        <template #icon>
          <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </template>
        {{ t('logs.export') }}
      </a-button>
    </div>

    <div class="bg-white rounded-xl p-4 shadow-sm">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <a-select v-model:value="filters.operation" placeholder="操作类型" allow-clear @change="loadLogs">
          <a-select-option value="create">创建</a-select-option>
          <a-select-option value="update">更新</a-select-option>
          <a-select-option value="delete">删除</a-select-option>
          <a-select-option value="upload">上传</a-select-option>
          <a-select-option value="bind">绑定</a-select-option>
          <a-select-option value="unbind">解绑</a-select-option>
          <a-select-option value="submit">提交审批</a-select-option>
          <a-select-option value="approve">审批通过</a-select-option>
          <a-select-option value="reject">驳回</a-select-option>
        </a-select>

        <a-select v-model:value="filters.result" placeholder="操作结果" allow-clear @change="loadLogs">
          <a-select-option value="success">{{ t('logs.success') }}</a-select-option>
          <a-select-option value="failed">{{ t('logs.failed') }}</a-select-option>
        </a-select>

        <a-select v-model:value="filters.module" placeholder="操作模块" allow-clear @change="loadLogs">
          <a-select-option value="厂区管理">厂区管理</a-select-option>
          <a-select-option value="线体管理">线体管理</a-select-option>
          <a-select-option value="工位管理">工位管理</a-select-option>
          <a-select-option value="设备管理">设备管理</a-select-option>
          <a-select-option value="现场结构">现场结构</a-select-option>
          <a-select-option value="设备绑定">设备绑定</a-select-option>
          <a-select-option value="驱动包管理">驱动包管理</a-select-option>
          <a-select-option value="AutoUnit包">AutoUnit包</a-select-option>
          <a-select-option value="审批管理">审批管理</a-select-option>
          <a-select-option value="界面管理">界面管理</a-select-option>
          <a-select-option value="部署清单管理">部署清单管理</a-select-option>
        </a-select>

        <a-input-search v-model:value="filters.search" placeholder="搜索操作人/描述" allow-clear @search="loadLogs" />
      </div>

      <div class="mt-4 flex gap-4">
        <a-range-picker v-model:value="dateRange" show-time format="YYYY-MM-DD HH:mm:ss" @change="handleDateChange" />
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <a-table :columns="columns" :data-source="logsData" :pagination="pagination" :loading="loading"
        @change="handleTableChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'operation'">
            <a-tag>{{ getOperationName(record.operation) }}</a-tag>
          </template>

          <template v-else-if="column.key === 'result'">
            <a-tag :color="record.result === 'success' ? 'success' : 'error'">
              {{ record.result === 'success' ? t('logs.success') : t('logs.failed') }}
            </a-tag>
          </template>

          <template v-else-if="column.key === 'operator'">
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs">
                {{ record.operator?.[0]?.toUpperCase() }}
              </div>
              <div>
                <div class="text-sm font-medium">{{ record.operator }}</div>
                <div class="text-xs text-gray-500">{{ record.role }}</div>
              </div>
            </div>
          </template>

          <template v-else-if="column.key === 'description'">
            <div class="max-w-md">
              <div class="text-sm text-gray-800">{{ record.description }}</div>
              <div v-if="record.error" class="text-xs text-red-500 mt-1">{{ record.error }}</div>
            </div>
          </template>

          <template v-else-if="column.key === 'actions'">
            <a-button size="small" type="link" @click="showDetail(record)">
              {{ t('logs.details') }}
            </a-button>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal v-model:open="detailModalVisible" title="日志详情" :footer="null" width="800px">
      <div v-if="currentLog" class="space-y-4">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="操作类型">
            <a-tag>{{ getOperationName(currentLog.operation) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="操作模块">{{ currentLog.module }}</a-descriptions-item>
          <a-descriptions-item label="操作人">{{ currentLog.operator }}</a-descriptions-item>
          <a-descriptions-item label="角色">{{ currentLog.role }}</a-descriptions-item>
          <a-descriptions-item label="操作结果">
            <a-tag :color="currentLog.result === 'success' ? 'success' : 'error'">
              {{ currentLog.result === 'success' ? '成功' : '失败' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="操作时间">{{ currentLog.time }}</a-descriptions-item>
          <a-descriptions-item label="IP地址">{{ currentLog.ip }}</a-descriptions-item>
          <a-descriptions-item label="User Agent" :span="2">
            <div class="text-xs break-all">{{ currentLog.userAgent }}</div>
          </a-descriptions-item>
          <a-descriptions-item label="描述" :span="2">{{ currentLog.description }}</a-descriptions-item>
          <a-descriptions-item v-if="currentLog.changes" label="变更内容" :span="2">
            <pre class="text-xs bg-gray-50 p-2 rounded">{{ JSON.stringify(currentLog.changes, null, 2) }}</pre>
          </a-descriptions-item>
          <a-descriptions-item v-if="currentLog.error" label="错误信息" :span="2">
            <div class="text-red-500">{{ currentLog.error }}</div>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import type { TableProps } from 'ant-design-vue'
import type { Dayjs } from 'dayjs'
import * as logsApi from '../api/logs'
import type { LogInfo, OperationType, OperationResult, OperationModule } from '../api/logs'

const { t } = useI18n()

const loading = ref(false)
const logsData = ref<LogInfo[]>([])
const detailModalVisible = ref(false)
const currentLog = ref<LogInfo | null>(null)
const dateRange = ref<[Dayjs, Dayjs] | null>(null)

const filters = reactive({
  search: '',
  operation: undefined as OperationType | undefined,
  result: undefined as OperationResult | undefined,
  module: undefined as OperationModule | undefined,
  startTime: '',
  endTime: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const columns = [
  { title: '操作类型', key: 'operation', width: 100 },
  { title: '操作模块', dataIndex: 'module', width: 120 },
  { title: '操作人', key: 'operator', width: 150 },
  { title: '描述', key: 'description', width: 300 },
  { title: '结果', key: 'result', width: 80 },
  { title: '操作时间', dataIndex: 'time', width: 180 },
  { title: '操作', key: 'actions', fixed: 'right', width: 100 }
]

const loadLogs = async () => {
  loading.value = true
  try {
    const response = await logsApi.getLogs({
      page: pagination.current,
      pageSize: pagination.pageSize,
      search: filters.search,
      operation: filters.operation,
      result: filters.result,
      module: filters.module,
      startTime: filters.startTime,
      endTime: filters.endTime
    })
    logsData.value = response.data.list
    pagination.total = response.data.total
  } catch (error) {
    console.error('加载日志失败:', error)
  } finally {
    loading.value = false
  }
}

const handleTableChange: TableProps['onChange'] = (pag) => {
  pagination.current = pag.current || 1
  pagination.pageSize = pag.pageSize || 20
  loadLogs()
}

const handleDateChange = (dates: any) => {
  if (dates && dates.length === 2) {
    filters.startTime = dates[0].format('YYYY-MM-DD HH:mm:ss')
    filters.endTime = dates[1].format('YYYY-MM-DD HH:mm:ss')
  } else {
    filters.startTime = ''
    filters.endTime = ''
  }
  loadLogs()
}

const getOperationName = (operation: string) => {
  const names: Record<string, string> = {
    create: '创建',
    update: '更新',
    delete: '删除',
    upload: '上传',
    bind: '绑定',
    unbind: '解绑',
    submit: '提交审批',
    approve: '审批通过',
    reject: '驳回'
  }
  return names[operation] || operation
}

const showDetail = async (record: LogInfo) => {
  try {
    const response = await logsApi.getLogDetail(record.id)
    currentLog.value = response.data
    detailModalVisible.value = true
  } catch (error) {
    console.error('获取日志详情失败:', error)
  }
}

const handleExport = async () => {
  try {
    const response = await logsApi.exportLogs({
      filters: {
        operation: filters.operation,
        result: filters.result,
        module: filters.module,
        startTime: filters.startTime,
        endTime: filters.endTime
      }
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    const fileName = `logs_${new Date().getTime()}.csv`
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    message.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
  }
}

onMounted(() => {
  loadLogs()
})
</script>
