<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-select
        v-model="classId"
        placeholder="选择班级"
        clearable
        filterable
        style="width: 220px"
        @change="(v: any) => { classId = v; page = 1; load() }"
      >
        <el-option
          v-for="c in classes"
          :key="c.id"
          :label="`${c.grade_name} · ${c.name}`"
          :value="c.id"
        />
      </el-select>
      <el-input
        v-model="keyword"
        placeholder="按学号或姓名搜索"
        clearable
        style="width: 220px"
        @keyup.enter="() => { page = 1; load() }"
      />
      <el-button @click="() => { page = 1; load() }">查询</el-button>
      <el-button v-if="userStore.isAdmin" type="primary" :icon="Plus" @click="openDialog()">
        新建学生
      </el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="student_no" label="学号" width="160" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="gender" label="性别" width="80" />
      <el-table-column prop="class_name" label="班级" width="120" />
      <el-table-column prop="birth_date" label="出生日期" width="120" />
      <el-table-column prop="parent_name" label="家长" width="100" />
      <el-table-column prop="parent_phone" label="家长电话" width="140" />
      <el-table-column v-if="userStore.isAdmin" label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editing?.id ? '编辑学生' : '新建学生'" width="540px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="学号" prop="student_no">
          <el-input v-model="form.student_no" :disabled="!!editing?.id" />
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
        <el-form-item label="班级" prop="class_id">
          <el-select v-model="form.class_id" filterable placeholder="选择班级">
            <el-option
              v-for="c in classes"
              :key="c.id"
              :label="`${c.grade_name} · ${c.name}`"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="出生日期">
          <el-date-picker v-model="form.birth_date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="家长姓名">
          <el-input v-model="form.parent_name" />
        </el-form-item>
        <el-form-item label="家长电话">
          <el-input v-model="form.parent_phone" />
        </el-form-item>
        <el-form-item label="入学日期">
          <el-date-picker v-model="form.enrollment_date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="2" />
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
  createStudent,
  deleteStudent,
  listClasses,
  listStudents,
  updateStudent,
  type Clazz,
  type Student,
} from '@/api/orgs'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const items = ref<Student[]>([])
const classes = ref<Clazz[]>([])
const classId = ref<number>()
const keyword = ref('')
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const dialogVisible = ref(false)
const editing = ref<Student | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  student_no: '',
  name: '',
  gender: '男',
  class_id: undefined as number | undefined,
  birth_date: '',
  parent_name: '',
  parent_phone: '',
  enrollment_date: '',
  note: '',
})

const rules: FormRules = {
  student_no: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  class_id: [{ required: true, message: '请选择班级', trigger: 'change' }],
}

async function loadOptions() {
  const c = await listClasses()
  classes.value = c.items
}

async function load() {
  loading.value = true
  try {
    const data = await listStudents({
      class_id: classId.value,
      keyword: keyword.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function openDialog(row?: Student) {
  editing.value = row || null
  Object.assign(form, {
    student_no: row?.student_no || '',
    name: row?.name || '',
    gender: row?.gender || '男',
    class_id: row?.class_id || classId.value,
    birth_date: row?.birth_date || '',
    parent_name: row?.parent_name || '',
    parent_phone: row?.parent_phone || '',
    enrollment_date: row?.enrollment_date || '',
    note: row?.note || '',
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
        await updateStudent(editing.value.id, form)
      } else {
        await createStudent(form)
      }
      ElMessage.success('已保存')
      dialogVisible.value = false
      await load()
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row: Student) {
  await ElMessageBox.confirm(`确定删除学生「${row.name}」？`, '删除', { type: 'warning' })
  await deleteStudent(row.id)
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
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
