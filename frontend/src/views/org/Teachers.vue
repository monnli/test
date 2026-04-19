<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-input
        v-model="keyword"
        placeholder="按工号或姓名搜索"
        clearable
        style="width: 220px"
        @keyup.enter="load"
      />
      <el-button @click="load">查询</el-button>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新建教师</el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="teacher_no" label="工号" width="140" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="gender" label="性别" width="80" />
      <el-table-column prop="title" label="职称" width="120">
        <template #default="{ row }">{{ row.title || '—' }}</template>
      </el-table-column>
      <el-table-column prop="phone" label="手机" width="140">
        <template #default="{ row }">{{ row.phone || '—' }}</template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="180">
        <template #default="{ row }">{{ row.email || '—' }}</template>
      </el-table-column>
      <el-table-column prop="username" label="关联账号" width="140">
        <template #default="{ row }">
          <el-tag v-if="row.username" type="success" size="small">{{ row.username }}</el-tag>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing?.id ? '编辑教师' : '新建教师'" width="540px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="工号" prop="teacher_no">
          <el-input v-model="form.teacher_no" :disabled="!!editing?.id" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio value="男">男</el-radio>
            <el-radio value="女">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="所属学校" prop="school_id">
          <el-select v-model="form.school_id" placeholder="选择学校" :disabled="!!editing?.id">
            <el-option v-for="s in schools" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="职称">
          <el-input v-model="form.title" placeholder="如：高级教师" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
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
  createTeacher,
  deleteTeacher,
  listSchools,
  listTeachers,
  updateTeacher,
  type School,
  type Teacher,
} from '@/api/orgs'

const items = ref<Teacher[]>([])
const schools = ref<School[]>([])
const keyword = ref('')
const loading = ref(false)

const dialogVisible = ref(false)
const editing = ref<Teacher | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  teacher_no: '',
  name: '',
  gender: '男',
  school_id: undefined as number | undefined,
  title: '',
  phone: '',
  email: '',
})

const rules: FormRules = {
  teacher_no: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  school_id: [{ required: true, message: '请选择学校', trigger: 'change' }],
}

async function loadSchools() {
  const data = await listSchools()
  schools.value = data.items
}

async function load() {
  loading.value = true
  try {
    const data = await listTeachers({ keyword: keyword.value || undefined })
    items.value = data.items
  } finally {
    loading.value = false
  }
}

function openDialog(row?: Teacher) {
  editing.value = row || null
  Object.assign(form, {
    teacher_no: row?.teacher_no || '',
    name: row?.name || '',
    gender: row?.gender || '男',
    school_id: row?.school_id || schools.value[0]?.id,
    title: row?.title || '',
    phone: row?.phone || '',
    email: row?.email || '',
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
        await updateTeacher(editing.value.id, form)
      } else {
        await createTeacher(form)
      }
      ElMessage.success('已保存')
      dialogVisible.value = false
      await load()
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row: Teacher) {
  await ElMessageBox.confirm(`确定删除教师「${row.name}」？`, '删除', { type: 'warning' })
  await deleteTeacher(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(async () => {
  await loadSchools()
  await load()
})
</script>

<style lang="scss" scoped>
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
</style>
