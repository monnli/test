<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-select v-model="teacherId" placeholder="按教师过滤" clearable filterable style="width: 200px" @change="load">
        <el-option v-for="t in teachers" :key="t.id" :label="`${t.name}（${t.teacher_no}）`" :value="t.id" />
      </el-select>
      <el-select v-model="classId" placeholder="按班级过滤" clearable style="width: 200px" @change="load">
        <el-option
          v-for="c in classes"
          :key="c.id"
          :label="`${c.grade_name} · ${c.name}`"
          :value="c.id"
        />
      </el-select>
      <el-select v-model="subjectId" placeholder="按科目过滤" clearable style="width: 160px" @change="load">
        <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-button @click="load">查询</el-button>
      <el-button type="primary" :icon="Plus" @click="openDialog">新增任课</el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="teacher_name" label="教师" />
      <el-table-column prop="grade_name" label="年级" />
      <el-table-column prop="class_name" label="班级" />
      <el-table-column prop="subject_name" label="科目" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button text type="danger" @click="onDelete(row)">解除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新增任课关系" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="教师" prop="teacher_id">
          <el-select v-model="form.teacher_id" filterable placeholder="选择教师">
            <el-option v-for="t in teachers" :key="t.id" :label="`${t.name}（${t.teacher_no}）`" :value="t.id" />
          </el-select>
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
        <el-form-item label="科目" prop="subject_id">
          <el-select v-model="form.subject_id" placeholder="选择科目">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
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
  createTcs,
  deleteTcs,
  listClasses,
  listSubjects,
  listTcs,
  listTeachers,
  type Clazz,
  type Subject,
  type Teacher,
  type TeacherClassSubject,
} from '@/api/orgs'

const items = ref<TeacherClassSubject[]>([])
const teachers = ref<Teacher[]>([])
const classes = ref<Clazz[]>([])
const subjects = ref<Subject[]>([])
const teacherId = ref<number>()
const classId = ref<number>()
const subjectId = ref<number>()
const loading = ref(false)

const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({
  teacher_id: undefined as number | undefined,
  class_id: undefined as number | undefined,
  subject_id: undefined as number | undefined,
})

const rules: FormRules = {
  teacher_id: [{ required: true, message: '请选择教师', trigger: 'change' }],
  class_id: [{ required: true, message: '请选择班级', trigger: 'change' }],
  subject_id: [{ required: true, message: '请选择科目', trigger: 'change' }],
}

async function loadOptions() {
  const [t, c, s] = await Promise.all([listTeachers(), listClasses(), listSubjects()])
  teachers.value = t.items
  classes.value = c.items
  subjects.value = s.items
}

async function load() {
  loading.value = true
  try {
    const data = await listTcs({
      teacher_id: teacherId.value,
      class_id: classId.value,
      subject_id: subjectId.value,
    })
    items.value = data.items
  } finally {
    loading.value = false
  }
}

function openDialog() {
  Object.assign(form, { teacher_id: undefined, class_id: undefined, subject_id: undefined })
  dialogVisible.value = true
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await createTcs(form)
      ElMessage.success('已新增')
      dialogVisible.value = false
      await load()
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row: TeacherClassSubject) {
  await ElMessageBox.confirm(
    `确定解除「${row.teacher_name}」在「${row.class_name}」的「${row.subject_name}」任课关系？`,
    '解除',
    { type: 'warning' },
  )
  await deleteTcs(row.id)
  ElMessage.success('已解除')
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
</style>
