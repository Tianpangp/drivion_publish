<template>
  <div class="max-w-4xl space-y-6">
    <div><h1 class="text-2xl font-semibold text-gray-900">个人中心</h1><p class="text-gray-500 mt-1">管理个人资料、密码和角色权限。</p></div>

    <a-alert v-if="isMockAccount" type="warning" show-icon message="当前为开发模拟账号" description="模拟账号仅用于登录和调试，不保存个人资料、角色申请或密码变更。" />

    <section v-if="isSso" class="bg-white border border-gray-200 rounded-lg p-6">
      <h2 class="text-base font-semibold mb-5">SSO 身份信息</h2>
      <a-descriptions :column="1" bordered size="small">
        <a-descriptions-item label="用户名">{{ userStore.user?.username }}</a-descriptions-item>
        <a-descriptions-item label="昵称">{{ userStore.user?.nickname || '-' }}</a-descriptions-item>
        <a-descriptions-item label="邮箱">{{ userStore.user?.email || '-' }}</a-descriptions-item>
        <a-descriptions-item label="角色">{{ userStore.user?.roles?.join('、') || userStore.user?.role }}</a-descriptions-item>
      </a-descriptions>
      <p class="text-sm text-gray-500 mt-4">个人资料、密码、账号状态和角色授权由 Drivion SSO 统一管理。</p>
    </section>

    <section v-if="!isMockAccount && !isSso" class="bg-white border border-gray-200 rounded-lg p-6">
      <h2 class="text-base font-semibold mb-5">个人资料</h2>
      <a-form layout="vertical" :model="profile" class="max-w-xl" @finish="saveProfile">
        <a-form-item label="用户名"><a-input :value="userStore.user?.username" disabled /></a-form-item>
        <a-form-item label="昵称"><a-input v-model:value="profile.nickname" /></a-form-item>
        <a-form-item label="邮箱"><a-input v-model:value="profile.email" type="email" /></a-form-item>
        <a-button type="primary" html-type="submit">保存资料</a-button>
      </a-form>
    </section>

    <section v-if="!isMockAccount && !isSso" class="bg-white border border-gray-200 rounded-lg p-6">
      <h2 class="text-base font-semibold mb-1">角色权限</h2>
      <p class="text-sm text-gray-500 mb-5">当前角色：{{ roleName(userStore.user?.role) }}</p>
      <a-form layout="vertical" :model="roleForm" class="max-w-xl" @finish="submitRoleRequest">
        <a-form-item label="申请角色" required><a-select v-model:value="roleForm.role" :options="roleOptions" /></a-form-item>
        <a-form-item label="申请原因"><a-textarea v-model:value="roleForm.reason" :rows="3" :maxlength="500" /></a-form-item>
        <a-button html-type="submit" :disabled="!roleForm.role">提交申请</a-button>
      </a-form>
      <a-table class="mt-6" size="small" :data-source="requests" :columns="requestColumns" row-key="id" :pagination="false" />
    </section>

    <section v-if="!isMockAccount && !isSso" class="bg-white border border-gray-200 rounded-lg p-6">
      <h2 class="text-base font-semibold mb-5">修改密码</h2>
      <a-form layout="vertical" :model="passwordForm" class="max-w-xl" @finish="savePassword">
        <a-form-item label="原密码" required><a-input-password v-model:value="passwordForm.oldPassword" /></a-form-item>
        <a-form-item label="新密码" required><a-input-password v-model:value="passwordForm.newPassword" /></a-form-item>
        <a-button html-type="submit">修改密码</a-button>
      </a-form>
    </section>

    <section v-if="!isMockAccount && !isSso" class="bg-white border border-red-200 rounded-lg p-6">
      <h2 class="text-base font-semibold text-red-700">注销账号</h2>
      <p class="text-sm text-gray-600 mt-2 mb-4">账号和个人资料将被永久删除，历史操作日志仍会保留。此操作不可恢复。</p>
      <a-button danger @click="confirmDelete">注销账号</a-button>
    </section>
    <a-modal v-model:open="deleteModalOpen" title="确认注销账号" ok-text="永久注销" ok-type="danger" @ok="deleteAccount">
      <p class="text-sm text-red-700 mb-3">此操作不可恢复，请输入当前密码确认。</p>
      <a-input-password v-model:value="deletePassword" placeholder="当前密码" />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import * as authApi from '../api/auth'
import type { RoleCode, RoleInfo, RoleRequestItem } from '../api/auth'
import { useUserStore } from '../stores/user'

const userStore = useUserStore(); const router = useRouter()
const roles = ref<RoleInfo[]>([]); const requests = ref<RoleRequestItem[]>([])
const profile = reactive({ nickname: userStore.user?.nickname || '', email: userStore.user?.email || '' })
const roleForm = reactive<{ role?: RoleCode; reason: string }>({ reason: '' })
const passwordForm = reactive({ oldPassword: '', newPassword: '' })
const deleteModalOpen = ref(false); const deletePassword = ref('')
const isMockAccount = computed(() => userStore.user?.id.startsWith('mock-') ?? false)
const isSso = computed(() => userStore.user?.authMode === 'sso')
const requestColumns = [{ title: '申请角色', dataIndex: 'requestedRole' }, { title: '状态', dataIndex: 'status' }, { title: '申请时间', dataIndex: 'createdAt' }]
const roleOptions = computed(() => roles.value.filter(r => r.code !== 'admin' && r.code !== userStore.user?.role).map(r => ({ value: r.code, label: r.name })))
const roleName = (code?: string) => roles.value.find(r => r.code === code)?.name || code || '-'
const load = async () => { if (isMockAccount.value || isSso.value) return; const [roleRes, requestRes] = await Promise.all([authApi.getRoles(), authApi.getMyRoleRequests()]); roles.value = roleRes.data; requests.value = requestRes.data }
const saveProfile = async () => { const res = await authApi.updateProfile({ nickname: profile.nickname, email: profile.email || undefined }); userStore.setUser(res.data); message.success('资料已保存') }
const submitRoleRequest = async () => { if (!roleForm.role) return; await authApi.applyRole(roleForm.role, roleForm.reason); roleForm.role = undefined; roleForm.reason = ''; await load(); message.success('角色申请已提交') }
const savePassword = async () => { await authApi.changePassword(passwordForm); passwordForm.oldPassword = ''; passwordForm.newPassword = ''; message.success('密码已修改') }
const confirmDelete = () => { deletePassword.value = ''; deleteModalOpen.value = true }
const deleteAccount = async () => { if (!deletePassword.value) { message.error('请输入密码'); return Promise.reject() }; await authApi.deleteAccount(deletePassword.value); userStore.clearLocal(); router.push('/login'); message.success('账号已注销') }
onMounted(load)
</script>
