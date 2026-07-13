<template>
  <div class="space-y-6">
    <div><h1 class="text-2xl font-semibold text-gray-900">用户管理</h1><p class="text-gray-500 mt-1">直接管理用户角色和账号状态，处理角色申请。</p></div>

    <section class="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div class="p-4 border-b border-gray-200 flex gap-3">
        <a-input-search v-model:value="filters.keyword" placeholder="用户名、昵称或邮箱" class="max-w-sm" @search="loadUsers" />
        <a-select v-model:value="filters.role" placeholder="全部角色" allow-clear class="w-44" :options="roleOptions" @change="loadUsers" />
        <a-select v-model:value="filters.status" placeholder="全部状态" allow-clear class="w-36" :options="statusOptions" @change="loadUsers" />
      </div>
      <a-table :data-source="users" :columns="userColumns" row-key="id" :pagination="pagination" @change="pageChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'user'"><div class="font-medium">{{ record.nickname || record.username }}</div><div class="text-xs text-gray-500">{{ record.username }} · {{ record.email || '无邮箱' }}</div></template>
          <template v-else-if="column.key === 'role'">
            <a-select :value="record.role" class="w-36" :options="allRoleOptions" @change="(role: RoleCode) => changeRole(record, role)" />
          </template>
          <template v-else-if="column.key === 'status'">
            <a-switch :checked="record.status === 'active'" checked-children="启用" un-checked-children="禁用" @change="(checked: boolean) => changeStatus(record, checked)" />
          </template>
        </template>
      </a-table>
    </section>

    <section class="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div class="px-4 py-3 border-b border-gray-200 flex items-center justify-between"><h2 class="font-semibold">待处理角色申请</h2><a-badge :count="requests.length" /></div>
      <a-table :data-source="requests" :columns="requestColumns" row-key="id" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'role'">{{ roleName(record.currentRole) }} → {{ roleName(record.requestedRole) }}</template>
          <template v-else-if="column.key === 'actions'"><a-space><a-button size="small" type="primary" @click="review(record, 'approve')">通过</a-button><a-button size="small" danger @click="review(record, 'reject')">驳回</a-button></a-space></template>
        </template>
      </a-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import * as authApi from '../api/auth'
import type { RoleCode, RoleInfo, RoleRequestItem, UserListItem } from '../api/auth'

const users = ref<UserListItem[]>([]); const roles = ref<RoleInfo[]>([]); const requests = ref<RoleRequestItem[]>([])
const filters = reactive<{ keyword: string; role?: string; status?: string }>({ keyword: '' })
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })
const userColumns = [{ title: '用户', key: 'user' }, { title: '角色', key: 'role', width: 180 }, { title: '状态', key: 'status', width: 150 }, { title: '注册时间', dataIndex: 'createTime', width: 180 }]
const requestColumns = [{ title: '用户', dataIndex: 'username' }, { title: '角色变更', key: 'role' }, { title: '原因', dataIndex: 'reason' }, { title: '申请时间', dataIndex: 'createdAt', width: 180 }, { title: '操作', key: 'actions', width: 150 }]
const statusOptions = [{ value: 'active', label: '启用' }, { value: 'inactive', label: '禁用' }]
const allRoleOptions = computed(() => roles.value.map(item => ({ value: item.code, label: item.name })))
const roleOptions = computed(() => allRoleOptions.value)
const roleName = (code: RoleCode) => roles.value.find(item => item.code === code)?.name || code
const loadUsers = async () => { const res = await authApi.searchUsers({ ...filters, page: pagination.current, pageSize: pagination.pageSize }); users.value = res.data.list; pagination.total = res.data.total }
const load = async () => { const [roleRes, requestRes] = await Promise.all([authApi.getRoles(), authApi.getRoleRequests()]); roles.value = roleRes.data; requests.value = requestRes.data; await loadUsers() }
const pageChange = (page: any) => { pagination.current = page.current; pagination.pageSize = page.pageSize; loadUsers() }
const changeRole = (user: UserListItem, role: RoleCode) => Modal.confirm({ title: '修改用户角色', content: `将 ${user.username} 的角色修改为 ${roleName(role)}？`, onOk: async () => { await authApi.changeUserRole(user.id, role); await loadUsers(); message.success('角色已更新') } })
const changeStatus = (user: UserListItem, checked: boolean) => Modal.confirm({ title: checked ? '启用用户' : '禁用用户', content: `${checked ? '启用' : '禁用'} ${user.username}？`, onOk: async () => { await authApi.changeUserStatus(user.id, checked ? 'active' : 'inactive'); await loadUsers(); message.success('用户状态已更新') }, onCancel: loadUsers })
const review = (item: RoleRequestItem, decision: 'approve' | 'reject') => Modal.confirm({ title: decision === 'approve' ? '通过角色申请' : '驳回角色申请', content: `${item.username}：${roleName(item.currentRole)} → ${roleName(item.requestedRole)}`, okType: decision === 'reject' ? 'danger' : 'primary', onOk: async () => { await authApi.reviewRoleRequest(item.id, decision); await load(); message.success('申请已处理') } })
onMounted(load)
</script>
