<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">审批中心</h1>
        <p class="text-gray-500 mt-1">处理 AutoUnit 包和 HAL 驱动包的转测、发布、下架审批</p>
      </div>
      <a-segmented v-model:value="activeQueue" :options="queueOptions" />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div v-for="item in summary" :key="item.label" class="bg-white border border-gray-200 rounded-lg p-4">
        <div class="text-sm text-gray-500">{{ item.label }}</div>
        <div class="text-2xl font-semibold text-gray-900 mt-2">{{ item.value }}</div>
      </div>
    </div>

    <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <a-table :columns="columns" :data-source="filteredRows" :pagination="false" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'artifact'">
            <div>
              <div class="font-medium text-gray-900">{{ record.name }}</div>
              <div class="text-xs text-gray-500 mt-1">{{ record.packageId }} / {{ record.version }}</div>
            </div>
          </template>
          <template v-else-if="column.key === 'type'">
            <a-tag :color="record.type === 'AutoUnit' ? 'purple' : 'blue'">{{ record.type }}</a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-tag :color="actionColor(record.action)">{{ record.action }}</a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag color="warning">{{ record.status }}</a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button size="small" type="primary" @click="approve(record)">通过</a-button>
              <a-button size="small" danger @click="reject(record)">驳回</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import * as publishApi from '../api/publish'
import type { ApprovalRow } from '../api/publish'

const activeQueue = ref('全部')
const queueOptions = ['全部', 'AutoUnit', 'HAL']

const rows = ref<ApprovalRow[]>([])

const columns = [
  { title: '制品', key: 'artifact' },
  { title: '类型', dataIndex: 'type', key: 'type', width: 120 },
  { title: '审批动作', dataIndex: 'action', key: 'action', width: 140 },
  { title: '申请人', dataIndex: 'applicant', key: 'applicant', width: 120 },
  { title: '提交时间', dataIndex: 'submittedAt', key: 'submittedAt', width: 180 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '操作', key: 'actions', fixed: 'right', width: 150 }
]

const filteredRows = computed(() => {
  if (activeQueue.value === '全部') return rows.value
  return rows.value.filter((item) => item.type === activeQueue.value)
})

const summary = computed(() => [
  { label: '待审批', value: rows.value.length },
  { label: 'AutoUnit', value: rows.value.filter((item) => item.type === 'AutoUnit').length },
  { label: 'HAL 驱动', value: rows.value.filter((item) => item.type === 'HAL').length },
  { label: '下架申请', value: rows.value.filter((item) => item.action === '申请下架').length }
])

const actionColor = (action: ApprovalRow['action']) => {
  if (action === '提交测试') return 'processing'
  if (action === '提交发布' || action === '重新上架') return 'success'
  return 'error'
}

const loadApprovals = async () => {
  const response = await publishApi.getApprovals(activeQueue.value)
  rows.value = response.data
}

const approve = async (row: ApprovalRow) => {
  await publishApi.approve(row.id)
  await loadApprovals()
  message.success(`${row.name} ${row.action}已通过`)
}

const reject = async (row: ApprovalRow) => {
  await publishApi.reject(row.id)
  await loadApprovals()
  message.success(`${row.name} 已退回原状态`)
}

watch(activeQueue, loadApprovals)
onMounted(loadApprovals)
</script>
