<template>
  <el-card shadow="never">
    <h3>上传课堂视频</h3>
    <el-form :model="form" label-width="100px" style="max-width: 600px">
      <el-form-item label="视频标题">
        <el-input v-model="form.title" placeholder="例：七年级一班 · 数学第二节课" />
      </el-form-item>
      <el-form-item label="所属班级">
        <el-select v-model="form.classId" filterable placeholder="可选">
          <el-option
            v-for="c in classes"
            :key="c.id"
            :label="`${c.grade_name} · ${c.name}`"
            :value="c.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="视频文件">
        <el-upload
          drag
          :auto-upload="false"
          :show-file-list="true"
          accept="video/*"
          :before-upload="beforeUpload"
          :on-change="onChange"
          :limit="1"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽或点击选择视频文件（支持 mp4 / avi / mov / mkv，最大 500 MB）</div>
        </el-upload>
      </el-form-item>
      <el-form-item label="抽帧间隔">
        <el-input-number v-model="form.interval" :min="0.5" :max="10" :step="0.5" />
        <span class="hint">秒（间隔越小越精细，演示建议 2 秒）</span>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="uploading" @click="onSubmit">上传并自动分析</el-button>
        <el-button @click="$router.back()">返回</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

import { listClasses, type Clazz } from '@/api/orgs'
import { startAnalyze, uploadVideo } from '@/api/classroom'

const router = useRouter()
const classes = ref<Clazz[]>([])
const uploading = ref(false)
const file = ref<File | null>(null)
const form = reactive({ title: '', classId: undefined as number | undefined, interval: 2.0 })

function beforeUpload() {
  return false
}

function onChange(f: any) {
  file.value = f.raw
}

async function onSubmit() {
  if (!file.value) {
    ElMessage.warning('请选择视频文件')
    return
  }
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file.value)
    if (form.title) fd.append('title', form.title)
    if (form.classId) fd.append('class_id', String(form.classId))
    const video = await uploadVideo(fd)
    ElMessage.success('上传成功，已自动提交分析')
    const task = await startAnalyze(video.id, form.interval)
    router.push(`/classroom/task/${task.id}`)
  } finally {
    uploading.value = false
  }
}

onMounted(async () => {
  const c = await listClasses()
  classes.value = c.items
})
</script>

<style lang="scss" scoped>
.hint {
  margin-left: 8px;
  font-size: 12px;
  color: #94a3b8;
}
</style>
