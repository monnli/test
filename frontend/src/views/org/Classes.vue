<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-select v-model="gradeId" placeholder="选择年级" clearable style="width: 180px" @change="load">
        <el-option v-for="g in grades" :key="g.id" :label="`${g.school_name} · ${g.name}`" :value="g.id" />
      </el-select>
      <el-button @click="load">查询</el-button>
      <el-button v-if="userStore.isAdmin" type="primary" :icon="Plus" @click="openDialog()">
        新建班级
      </el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="grade_name" label="年级" width="120" />
      <el-table-column prop="name" label="班级名称" min-width="140" />
      <el-table-column prop="head_teacher_name" label="班主任" width="160">
        <template #default="{ row }">{{ row.head_teacher_name || '—' }}</template>
      </el-table-column>
      <el-table-column prop="student_count" label="学生数" width="100" />
      <el-table-column v-if="userStore.isAdmin" label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing?.id ? '编辑班级' : '新建班级'" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="所属年级" prop="grade_id">
          <el-select v-model="form.grade_id" placeholder="选择年级" :disabled="!!editing?.id">
            <el-option v-for="g in grades" :key="g.id" :label="`${g.school_name} · ${g.name}`" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级名称" prop="name">
          <el-input v-model="form.name" placeholder="如：1 班" />
        </el-form-item>
        <el-form-item label="班主任">
          <el-select v-model="form.head_teacher_id" placeholder="可选" clearable filterable>
            <el-option v-for="t in teachers" :key="t.id" :label="`${t.name}（${t.teacher_no}）`" :value="t.id" />
          </el-select>
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
  createClass,
  deleteClass,
  listClasses,
  listGrades,
  listTeachers,
  updateClass,
  type Clazz,
  type Grade,
  type Teacher,
} from '@/api/orgs'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const items = ref<Clazz[]>([])
const grades = ref<Grade[]>([])
const teachers = ref<Teacher[]>([])
const gradeId = ref<number>()
const loading = ref(false)

const dialogVisible = ref(false)
const editing = ref<Clazz | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  grade_id: undefined as number | undefined,
  name: '',
  head_teacher_id: undefined as number | undefined | null,
})

const rules: FormRules = {
  grade_id: [{ required: true, message: '请选择年级', trigger: 'change' }],
  name: [{ required: true, message: '请输入班级名称', trigger: 'blur' }],
}

async function loadOptions() {
  const [g, t] = await Promise.all([listGrades(), listTeachers()])
  grades.value = g.items
  teachers.value = t.items
}

async function load() {
  loading.value = true
  try {
    const data = await listClasses(gradeId.value ? { grade_id: gradeId.value } : undefined)
    items.value = data.items
  } finally {
    loading.value = false
  }
}

function openDialog(row?: Clazz) {
  editing.value = row || null
  Object.assign(form, {
    grade_id: row?.grade_id || gradeId.value,
    name: row?.name || '',
    head_teacher_id: row?.head_teacher_id ?? undefined,
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
        await updateClass(editing.value.id, {
          name: form.name,
          head_teacher_id: form.head_teacher_id,
        })
      } else {
        await createClass(form)
      }
      ElMessage.success('已保存')
      dialogVisible.value = false
      await load()
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row: Clazz) {
  await ElMessageBox.confirm(`确定删除班级「${row.name}」？`, '删除', { type: 'warning' })
  await deleteClass(row.id)
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
}
</style>
