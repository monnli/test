<template>
  <el-card shadow="never">
    <template #header>
      <div class="head">
        <span class="card-title">视频 #{{ videoId }} 的分析任务记录</span>
        <el-button type="primary" @click="onAnalyze">重新分析</el-button>
      </div>
    </template>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="任务 ID" width="100" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" effect="dark">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="进度" width="240">
        <template #default="{ row }">
          <el-progress :percentage="row.progress" />
        </template>
      </el-table-column>
      <el-table-column prop="processed_frames" label="已处理帧" width="120" />
      <el-table-column prop="total_frames" label="总帧" width="100" />
      <el-table-column prop="started_at" label="开始时间" width="170" />
      <el-table-column prop="finished_at" label="完成时间" width="170" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button text type="primary" @click="$router.push(`/classroom/task/${row.id}`)">
            查看报告
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { listVideoTasks, startAnalyze, type AnalysisTaskItem } from '@/api/classroom'

const route = useRoute()
const router = useRouter()
const videoId = computed(() => Number(route.params.videoId))
const items = ref<AnalysisTaskItem[]>([])
const loading = ref(false)

function statusTag(s: string): any {
  return { pending: 'info', running: 'warning', success: 'success', failed: 'danger' }[s] || 'info'
}
function statusLabel(s: string) {
  return { pending: '排队中', running: '运行中', success: '已完成', failed: '失败' }[s] || s
}

async function load() {
  loading.value = true
  try {
    const data = await listVideoTasks(videoId.value)
    items.value = data.items
  } finally {
    loading.value = false
  }
}

async function onAnalyze() {
  const t = await startAnalyze(videoId.value)
  ElMessage.success('已提交')
  router.push(`/classroom/task/${t.id}`)
}

onMounted(load)
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
