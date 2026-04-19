<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-button @click="load">刷新</el-button>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新建科目</el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="科目名称" />
      <el-table-column prop="code" label="编码" />
      <el-table-column prop="sort_order" label="排序" width="100" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing?.id ? '编辑科目' : '新建科目'" width="420px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="编码">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
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
  createSubject,
  deleteSubject,
  listSubjects,
  updateSubject,
  type Subject,
} from '@/api/orgs'

const items = ref<Subject[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref<Subject | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({ name: '', code: '', sort_order: 0 })
const rules: FormRules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try {
    const data = await listSubjects()
    items.value = data.items
  } finally {
    loading.value = false
  }
}

function openDialog(row?: Subject) {
  editing.value = row || null
  Object.assign(form, {
    name: row?.name || '',
    code: row?.code || '',
    sort_order: row?.sort_order || 0,
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
        await updateSubject(editing.value.id, form)
      } else {
        await createSubject(form)
      }
      ElMessage.success('已保存')
      dialogVisible.value = false
      await load()
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row: Subject) {
  await ElMessageBox.confirm(`确定删除科目「${row.name}」？`, '删除', { type: 'warning' })
  await deleteSubject(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<style lang="scss" scoped>
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
</style>
