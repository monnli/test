<template>
  <el-card shadow="never">
    <template #header>
      <div class="head">
        <span class="card-title">摄像头管理</span>
        <el-button v-if="userStore.isAdmin" type="primary" :icon="Plus" @click="openDialog()">
          新建摄像头
        </el-button>
      </div>
    </template>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="class_name" label="绑定班级" />
      <el-table-column prop="location" label="位置" />
      <el-table-column prop="stream_type" label="流类型" width="110" />
      <el-table-column prop="stream_url" label="视频流地址" min-width="260" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'online' ? 'success' : 'info'" effect="dark" size="small">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="userStore.isAdmin" label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="editing?.id ? '编辑摄像头' : '新建摄像头'"
      width="560px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="如：七1班教室前置" />
        </el-form-item>
        <el-form-item label="所属学校" prop="school_id">
          <el-select v-model="form.school_id" placeholder="选择学校">
            <el-option v-for="s in schools" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="绑定班级">
          <el-select v-model="form.class_id" filterable clearable placeholder="可选">
            <el-option
              v-for="c in classes"
              :key="c.id"
              :label="`${c.grade_name} · ${c.name}`"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" placeholder="教室前方 / 后方 / 侧面" />
        </el-form-item>
        <el-form-item label="视频流类型" prop="stream_type">
          <el-radio-group v-model="form.stream_type">
            <el-radio value="rtsp">RTSP</el-radio>
            <el-radio value="hls">HLS</el-radio>
            <el-radio value="file_loop">本地视频循环</el-radio>
            <el-radio value="file">本地视频一次</el-radio>
            <el-radio value="webrtc">WebRTC</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="视频流地址" prop="stream_url">
          <el-input
            v-model="form.stream_url"
            placeholder="rtsp://user:pass@ip:554/..  或 storage/demo_videos/xxx.mp4"
          />
        </el-form-item>
        <el-form-item label="分辨率">
          <el-input v-model="form.resolution" placeholder="1280x720" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-radio-group v-model="form.status">
            <el-radio value="online">在线</el-radio>
            <el-radio value="offline">离线</el-radio>
            <el-radio value="disabled">禁用</el-radio>
          </el-radio-group>
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
  createCamera,
  deleteCamera,
  listCameras,
  updateCamera,
  type Camera,
} from '@/api/m10'
import { listClasses, listSchools, type Clazz, type School } from '@/api/orgs'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const items = ref<Camera[]>([])
const classes = ref<Clazz[]>([])
const schools = ref<School[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const editing = ref<Camera | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  school_id: undefined as number | undefined,
  class_id: undefined as number | undefined | null,
  location: '',
  stream_type: 'file_loop',
  stream_url: '',
  resolution: '',
  status: 'online',
  note: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  school_id: [{ required: true, message: '请选择学校', trigger: 'change' }],
  stream_type: [{ required: true, message: '请选择流类型', trigger: 'change' }],
  stream_url: [{ required: true, message: '请填写视频流地址', trigger: 'blur' }],
}

async function loadOpts() {
  const [s, c] = await Promise.all([listSchools(), listClasses()])
  schools.value = s.items
  classes.value = c.items
}

async function load() {
  loading.value = true
  try {
    items.value = (await listCameras()).items
  } finally {
    loading.value = false
  }
}

function openDialog(row?: Camera) {
  editing.value = row || null
  Object.assign(form, {
    name: row?.name || '',
    school_id: row?.school_id || schools.value[0]?.id,
    class_id: row?.class_id ?? undefined,
    location: row?.location || '',
    stream_type: row?.stream_type || 'file_loop',
    stream_url: row?.stream_url || '',
    resolution: row?.resolution || '',
    status: row?.status || 'online',
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
        await updateCamera(editing.value.id, form)
      } else {
        await createCamera(form)
      }
      ElMessage.success('已保存')
      dialogVisible.value = false
      await load()
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row: Camera) {
  await ElMessageBox.confirm(`确定删除摄像头「${row.name}」？`, '删除', { type: 'warning' })
  await deleteCamera(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(async () => {
  await loadOpts()
  await load()
})
</script>

<style lang="scss" scoped>
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .card-title {
    font-weight: 600;
  }
}
</style>
