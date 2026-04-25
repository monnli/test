<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-input
        v-model="keyword"
        placeholder="按名称或编码搜索"
        style="width: 240px"
        clearable
        @keyup.enter="load"
      />
      <el-button @click="load">查询</el-button>
      <el-button v-if="isSuper" type="primary" :icon="Plus" @click="openDialog()">新建学校</el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="学校名称" min-width="180" />
      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
      <el-table-column prop="contact" label="联系人" width="120" />
      <el-table-column prop="phone" label="联系电话" width="140" />
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="editing?.id ? '编辑学校' : '新建学校'"
      width="520px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="学校名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="编码">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.description" type="textarea" :rows="2" />
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

import { listSchools, createSchool, updateSchool, deleteSchool, type School } from '@/api/orgs'
import { useUserStore } from '@/stores/user'

const items = ref<School[]>([])
const loading = ref(false)
const keyword = ref('')
const userStore = useUserStore()
const isSuper = computed(() => Boolean(userStore.userInfo?.is_super))

const dialogVisible = ref(false)
const editing = ref<School | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  code: '',
  address: '',
  contact: '',
  phone: '',
  description: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入学校名称', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const data = await listSchools({ keyword: keyword.value || undefined })
    items.value = data.items
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.assign(form, { name: '', code: '', address: '', contact: '', phone: '', description: '' })
}

function openDialog(row?: School) {
  if (!isSuper.value && !row) {
    ElMessage.warning('仅超级管理员可新建学校')
    return
  }
  editing.value = row || null
  resetForm()
  if (row) Object.assign(form, row)
  dialogVisible.value = true
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (editing.value?.id) {
        await updateSchool(editing.value.id, form)
        ElMessage.success('已更新')
      } else {
        await createSchool(form)
        ElMessage.success('已创建')
      }
      dialogVisible.value = false
      await load()
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row: School) {
  await ElMessageBox.confirm(`确定删除学校「${row.name}」？`, '删除', { type: 'warning' })
  await deleteSchool(row.id)
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
