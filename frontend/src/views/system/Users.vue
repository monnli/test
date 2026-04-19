<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-input
        v-model="keyword"
        placeholder="按账号或姓名搜索"
        clearable
        style="width: 220px"
        @keyup.enter="() => { page = 1; load() }"
      />
      <el-select v-model="roleCode" placeholder="按角色过滤" clearable style="width: 200px" @change="() => { page = 1; load() }">
        <el-option v-for="r in roles" :key="r.code" :label="r.name" :value="r.code" />
      </el-select>
      <el-button @click="() => { page = 1; load() }">查询</el-button>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新建用户</el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="username" label="账号" width="150" />
      <el-table-column prop="real_name" label="姓名" width="120" />
      <el-table-column label="角色" min-width="180">
        <template #default="{ row }">
          <el-tag
            v-for="r in row.roles"
            :key="r.code"
            size="small"
            type="success"
            effect="plain"
            class="role-tag"
          >
            {{ r.name }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="手机" width="140">
        <template #default="{ row }">{{ row.phone || '—' }}</template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="180">
        <template #default="{ row }">{{ row.email || '—' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" effect="dark" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_login_at" label="最后登录" width="180">
        <template #default="{ row }">{{ row.last_login_at || '—' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button text type="warning" @click="onResetPwd(row)">重置密码</el-button>
          <el-button text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="load"
        @size-change="load"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editing?.id ? '编辑用户' : '新建用户'" width="540px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" :disabled="!!editing?.id" />
        </el-form-item>
        <el-form-item v-if="!editing?.id" label="初始密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="所属学校">
          <el-select v-model="form.school_id" placeholder="选择学校" clearable>
            <el-option v-for="s in schools" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色" prop="role_codes">
          <el-checkbox-group v-model="form.role_codes">
            <el-checkbox
              v-for="r in roles"
              :key="r.code"
              :value="r.code"
              :label="r.code"
            >
              {{ r.name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

import {
  createUser,
  deleteUser,
  listAllRoles,
  listUsers,
  resetUserPassword,
  updateUser,
  type RoleItem,
  type UserItem,
} from '@/api/users'
import { listSchools, type School } from '@/api/orgs'

const items = ref<UserItem[]>([])
const roles = ref<RoleItem[]>([])
const schools = ref<School[]>([])
const keyword = ref('')
const roleCode = ref('')
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const dialogVisible = ref(false)
const editing = ref<UserItem | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  password: '',
  real_name: '',
  school_id: undefined as number | undefined,
  role_codes: [] as string[],
  phone: '',
  email: '',
  is_active: true,
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role_codes: [
    {
      validator: (_r, value, cb) =>
        Array.isArray(value) && value.length > 0 ? cb() : cb(new Error('至少选择一个角色')),
      trigger: 'change',
    },
  ],
}

async function loadOptions() {
  const [r, s] = await Promise.all([listAllRoles(), listSchools()])
  roles.value = r.items.filter((it) => it.code !== 'super_admin')
  schools.value = s.items
}

async function load() {
  loading.value = true
  try {
    const data = await listUsers({
      keyword: keyword.value || undefined,
      role_code: roleCode.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function openDialog(row?: UserItem) {
  editing.value = row || null
  Object.assign(form, {
    username: row?.username || '',
    password: '',
    real_name: row?.real_name || '',
    school_id: row?.school_id || undefined,
    role_codes: row ? row.roles.map((r) => r.code) : [],
    phone: row?.phone || '',
    email: row?.email || '',
    is_active: row ? row.is_active : true,
  })
  dialogVisible.value = true
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (editing.value?.id) {
        const { password: _pwd, username: _u, ...rest } = form
        await updateUser(editing.value.id, rest)
      } else {
        await createUser(form)
      }
      ElMessage.success('已保存')
      dialogVisible.value = false
      await load()
    } finally {
      submitting.value = false
    }
  })
}

async function onResetPwd(row: UserItem) {
  const result = await ElMessageBox.prompt(
    `为「${row.username}」设置新密码`,
    '重置密码',
    { inputType: 'password', confirmButtonText: '重置', cancelButtonText: '取消' },
  )
  await resetUserPassword(row.id, result.value)
  ElMessage.success('已重置')
}

async function onDelete(row: UserItem) {
  await ElMessageBox.confirm(`确定删除用户「${row.username}」？`, '删除', { type: 'warning' })
  await deleteUser(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(async () => {
  await loadOptions()
  await load()
})
</script>

<style lang="scss" scoped>
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.role-tag {
  margin-right: 4px;
}
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
