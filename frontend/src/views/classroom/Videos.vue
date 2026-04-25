<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-button type="primary" :icon="Upload" @click="$router.push('/classroom/upload')">
        上传新视频
      </el-button>
      <el-button :icon="VideoCamera" @click="$router.push('/classroom/realtime')">
        实时摄像头分析
      </el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column label="时长" width="100">
        <template #default="{ row }">
          {{ formatDuration(row.duration_seconds) }}
        </template>
      </el-table-column>
      <el-table-column prop="size_mb" label="大小" width="100">
        <template #default="{ row }">{{ row.size_mb }} MB</template>
      </el-table-column>
      <el-table-column label="分辨率" width="120">
        <template #default="{ row }">
          <span v-if="row.width">{{ row.width }} × {{ row.height }}</span>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="上传时间" width="170" />
      <el-table-column label="操作" width="320" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="onAnalyze(row)">分析</el-button>
          <el-button text type="success" @click="$router.push(`/classroom/video/${row.id}`)">
            分析记录
          </el-button>
          <el-button text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="load"
        @size-change="load"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, VideoCamera } from '@element-plus/icons-vue'

import { deleteVideo, listVideos, startAnalyze, type VideoItem } from '@/api/classroom'

const router = useRouter()
const items = ref<VideoItem[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

function formatDuration(s: number) {
  if (!s) return '—'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${String(sec).padStart(2, '0')}`
}

async function load() {
  loading.value = true
  try {
    const data = await listVideos({ page: page.value, page_size: pageSize.value })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function onAnalyze(row: VideoItem) {
  const task = await startAnalyze(row.id)
  ElMessage.success('分析任务已提交')
  router.push(`/classroom/task/${task.id}`)
}

async function onDelete(row: VideoItem) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.title}」？将同时删除文件及关联分析记录。`, '删除视频', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await deleteVideo(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style lang="scss" scoped>
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
