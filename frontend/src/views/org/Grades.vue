<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-select v-model="schoolId" placeholder="选择学校" clearable style="width: 220px" @change="load">
        <el-option v-for="s in schools" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-button @click="load">查询</el-button>
      <el-button v-if="userStore.isAdmin" type="primary" :icon="Plus" @click="openDialog()">
        新建年级
      </el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="school_name" label="学校" min-width="160" />
      <el-table-column prop="name" label="年级名称" min-width="140" />
      <el-table-column prop="level" label="年级级别" width="100" />
      <el-table-column prop="class_count" label="班级数" width="100" />
      <el-table-column v-if="userStore.isAdmin" label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="editing?.id ? '编辑年级' : '新建年级'"
      width="460px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="所属学校" prop="school_id">
          <el-select v-model="form.school_id" placeholder="选择学校" :disabled="!!editing?.id">
            <el-option v-for="s in schools" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="年级名称" prop="name">
          <el-input v-model="form.name" placeholder="如：七年级" />
        </el-form-item>
        <el-form-item label="年级级别" prop="level">
          <el-input-number v-model="form.level" :min="1" :max="12" />
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
  createGrade,
  deleteGrade,
  listGrades,
  listSchools,
  updateGrade,
  type Grade,
  type School,
} from '@/api/orgs'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const items = ref<Grade[]>([])
const schools = ref<School[]>([])
const schoolId = ref<number>()
const loading = ref(false)

const dialogVisible = ref(false)
const editing = ref<Grade | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({ school_id: undefined as number | undefined, name: '', level: 7 })
const rules: FormRules = {
  school_id: [{ required: true, message: '请选择学校', trigger: 'change' }],
  name: [{ required: true, message: '请输入年级名称', trigger: 'blur' }],
}

async function loadSchools() {
  const data = await listSchools()
  schools.value = data.items
  if (!schoolId.value && schools.value[0]) schoolId.value = schools.value[0].id
}

async function load() {
  loading.value = true
  try {
    const data = await listGrades(schoolId.value ? { school_id: schoolId.value } : undefined)
    items.value = data.items
  } finally {
    loading.value = false
  }
}

function openDialog(row?: Grade) {
  editing.value = row || null
  Object.assign(form, {
    school_id: row?.school_id || schoolId.value,
    name: row?.name || '',
    level: row?.level || 7,
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
        await updateGrade(editing.value.id, { name: form.name, level: form.level })
      } else {
        await createGrade({ school_id: form.school_id, name: form.name, level: form.level })
      }
      ElMessage.success('已保存')
      dialogVisible.value = false
      await load()
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row: Grade) {
  await ElMessageBox.confirm(`确定删除年级「${row.name}」？`, '删除', { type: 'warning' })
  await deleteGrade(row.id)
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
