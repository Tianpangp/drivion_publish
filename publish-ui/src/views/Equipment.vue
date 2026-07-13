<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">设备绑定</h1>
        <p class="text-gray-500 mt-1">按设备实例维护 AutoUnit 绑定关系，设备归属路径为厂区 / 线体 / 工位 / 设备</p>
      </div>
      <a-button v-if="canBind" type="primary" :disabled="!activeEquipment" @click="showBindingDrawer(activeEquipment)">
        绑定 AutoUnit
      </a-button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-5">
      <section class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-200">
          <a-input-search v-model:value="keyword" placeholder="搜索设备、工位、线体" allow-clear />
        </div>
        <div class="p-3 space-y-2 max-h-[calc(100vh-230px)] overflow-y-auto">
          <button
            v-for="item in filteredEquipment"
            :key="item.id"
            class="w-full text-left rounded-md border px-3 py-3 transition-colors"
            :class="selectedEquipment?.id === item.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'"
            @click="selectedEquipment = item"
          >
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="font-medium text-gray-800">{{ item.name }}</div>
                <div class="text-xs text-gray-500 mt-1">{{ item.code }}</div>
              </div>
              <a-tag :color="item.enabled ? 'success' : 'default'">{{ item.enabled ? '启用' : '停用' }}</a-tag>
            </div>
            <div class="text-xs text-gray-500 mt-2 leading-5">{{ item.path }}</div>
          </button>
        </div>
      </section>

      <section v-if="activeEquipment" class="space-y-5">
        <div class="bg-white rounded-lg border border-gray-200 p-5">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div class="text-sm text-gray-500">当前设备</div>
              <h2 class="text-xl font-semibold text-gray-900 mt-1">{{ activeEquipment.name }}</h2>
              <div class="text-sm text-gray-500 mt-2">{{ activeEquipment.path }}</div>
            </div>
            <a-space v-if="canBind">
              <a-button @click="showBindingDrawer(activeEquipment)">替换版本</a-button>
              <a-button danger @click="unbind(activeEquipment)">解绑</a-button>
            </a-space>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mt-5">
            <div class="border border-gray-200 rounded-md p-3">
              <div class="text-xs text-gray-500">设备编号</div>
              <div class="font-medium text-gray-800 mt-1">{{ activeEquipment.code }}</div>
            </div>
            <div class="border border-gray-200 rounded-md p-3">
              <div class="text-xs text-gray-500">类型</div>
              <div class="font-medium text-gray-800 mt-1">{{ activeEquipment.type }}</div>
            </div>
            <div class="border border-gray-200 rounded-md p-3">
              <div class="text-xs text-gray-500">厂商 / 型号</div>
              <div class="font-medium text-gray-800 mt-1">{{ activeEquipment.vendor }} / {{ activeEquipment.model }}</div>
            </div>
            <div class="border border-gray-200 rounded-md p-3">
              <div class="text-xs text-gray-500">管理状态</div>
              <div class="font-medium text-gray-800 mt-1">{{ activeEquipment.enabled ? '启用' : '停用' }}</div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-gray-200 p-5">
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold text-gray-900">AutoUnit 当前绑定</h3>
            <a-tag v-if="activeEquipment.binding" :color="statusColor(activeEquipment.binding.status)">
              {{ statusText(activeEquipment.binding.status) }}
            </a-tag>
          </div>

          <a-empty v-if="!activeEquipment.binding" class="py-8" description="未绑定 AutoUnit 包" />

          <div
            v-else
            class="relative mt-4 border rounded-md overflow-hidden"
            :class="activeEquipment.binding.status !== 'published' ? 'border-red-200 bg-red-50/30' : 'border-gray-200'"
          >
            <div
              v-if="activeEquipment.binding.status !== 'published'"
              class="pointer-events-none absolute inset-0 flex items-center justify-center text-5xl font-black text-red-500/10 tracking-widest rotate-[-8deg]"
            >
              未发布
            </div>
            <div class="grid grid-cols-1 md:grid-cols-[minmax(0,2fr)_120px_minmax(180px,1fr)_160px]">
              <div class="p-4 min-w-0">
                <div class="font-medium text-gray-900 break-words">{{ activeEquipment.binding.name }}</div>
                <div class="text-sm text-gray-500 mt-1 break-all">{{ activeEquipment.binding.packageId }}</div>
              </div>
              <div class="p-4 border-t md:border-t-0 md:border-l border-gray-200">
                <div class="text-xs text-gray-500">版本</div>
                <div class="font-mono text-sm mt-1 break-all">{{ activeEquipment.binding.version }}</div>
              </div>
              <div class="p-4 border-t md:border-t-0 md:border-l border-gray-200 min-w-0">
                <div class="text-xs text-gray-500">模块</div>
                <div class="font-mono text-sm mt-1 break-all leading-5">{{ activeEquipment.binding.module }}</div>
              </div>
              <div class="p-4 border-t md:border-t-0 md:border-l border-gray-200">
                <div class="text-xs text-gray-500">绑定时间</div>
                <div class="text-sm mt-1">{{ activeEquipment.binding.boundAt }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-gray-200 p-5">
          <h3 class="text-base font-semibold text-gray-900 mb-4">绑定历史</h3>
          <a-table :columns="historyColumns" :data-source="activeEquipment.history" :pagination="false" size="small" />
        </div>
      </section>
      <a-empty v-else class="bg-white rounded-lg border border-gray-200 py-16" description="暂无设备数据" />
    </div>

    <a-drawer v-model:open="drawerOpen" title="绑定 AutoUnit 包版本" width="620">
      <div class="space-y-4">
        <a-alert
          type="info"
          show-icon
          message="一个设备只能绑定一个 AutoUnit 包版本；新绑定会替换旧绑定。"
        />
        <a-radio-group v-model:value="selectedPackageId" class="w-full">
          <div class="space-y-3">
            <label
              v-for="pkg in packageOptions"
              :key="pkg.id"
              class="block rounded-md border p-4 cursor-pointer"
              :class="selectedPackageId === pkg.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'"
            >
              <div class="flex items-start gap-3">
                <a-radio :value="pkg.id" class="mt-1" />
                <div class="flex-1">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <div class="font-medium text-gray-900">{{ pkg.name }}</div>
                      <div class="text-xs text-gray-500 mt-1 break-all leading-5">{{ pkg.packageId }} / {{ pkg.module }}</div>
                    </div>
                    <a-tag :color="statusColor(pkg.status)">{{ statusText(pkg.status) }}</a-tag>
                  </div>
                  <div class="mt-2 text-sm text-gray-600">版本 {{ pkg.version }}</div>
                  <div v-if="pkg.status !== 'published'" class="mt-2 text-xs text-red-600">未发布版本，绑定后需要在设备列表标红。</div>
                </div>
              </div>
            </label>
          </div>
        </a-radio-group>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <a-button @click="drawerOpen = false">取消</a-button>
          <a-button type="primary" @click="bindPackage">保存绑定</a-button>
        </div>
      </template>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import * as publishApi from '../api/publish'
import type { AutoUnitBinding, EquipmentRow, PackageStatus } from '../api/publish'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const canBind = computed(() => userStore.hasPermission('binding:autounit:manage'))

const equipmentRows = ref<EquipmentRow[]>([])
const packageOptions = ref<AutoUnitBinding[]>([])

const keyword = ref('')
const selectedEquipment = ref<EquipmentRow | null>(null)
const drawerOpen = ref(false)
const drawerTarget = ref<EquipmentRow | null>(null)
const selectedPackageId = ref<string>()

const filteredEquipment = computed(() => {
  const value = keyword.value.trim().toLowerCase()
  if (!value) return equipmentRows.value
  return equipmentRows.value.filter((item) =>
    [item.name, item.code, item.path, item.type].some((text) => text.toLowerCase().includes(value))
  )
})

const activeEquipment = computed<EquipmentRow | null>(() => selectedEquipment.value)

const historyColumns = [
  { title: '时间', dataIndex: 'time', key: 'time' },
  { title: '动作', dataIndex: 'action', key: 'action' },
  { title: '包 ID', dataIndex: 'package', key: 'package' },
  { title: '版本', dataIndex: 'version', key: 'version' },
  { title: '操作人', dataIndex: 'operator', key: 'operator' }
]

const statusColor = (status: PackageStatus) => {
  if (status === 'published') return 'success'
  if (status === 'testing') return 'processing'
  if (status === 'pending_testing' || status === 'pending_publish') return 'warning'
  if (status === 'removed') return 'default'
  return 'warning'
}

const statusText = (status: PackageStatus) => {
  const map: Record<PackageStatus, string> = {
    pending_testing: '待测试',
    testing: '已测试',
    pending_publish: '待发布',
    pending_remove: '待下架',
    published: '已发布',
    removed: '已下架'
  }
  return map[status]
}

const loadData = async () => {
  const [equipmentResponse, packageResponse] = await Promise.all([
    publishApi.getEquipment(),
    publishApi.getAutoUnitPackageOptions()
  ])
  equipmentRows.value = equipmentResponse.data
  packageOptions.value = packageResponse.data.list.filter((item) => !item.deleted).map((item) => ({
    id: item.id,
    name: item.name,
    packageId: item.packageId || item.name,
    version: item.version,
    module: item.module || '-',
    status: item.status,
    boundAt: '-'
  }))
  selectedEquipment.value = equipmentRows.value[0] || null
}

const showBindingDrawer = (equipment: EquipmentRow | null) => {
  if (!equipment) return
  drawerTarget.value = equipment
  selectedPackageId.value = equipment.binding?.id
  drawerOpen.value = true
}

const bindPackage = async () => {
  if (!drawerTarget.value || !selectedPackageId.value) {
    message.error('请选择 AutoUnit 包版本')
    return
  }
  const pkg = packageOptions.value.find((item) => item.id === selectedPackageId.value)
  if (!pkg) return

  await publishApi.bindEquipmentAutoUnit(drawerTarget.value.id, pkg.id)
  await loadData()
  drawerOpen.value = false
  message.success(pkg.status === 'published' ? '绑定成功' : '绑定成功，未发布版本已标红提示')
}

const unbind = async (equipment: EquipmentRow | null) => {
  if (!equipment) return
  if (!equipment.binding) {
    message.info('当前设备未绑定 AutoUnit')
    return
  }
  await publishApi.unbindEquipmentAutoUnit(equipment.id)
  await loadData()
  message.success('已解绑')
}

onMounted(loadData)
</script>
