<template>
  <div class="wall-page">
    <el-card shadow="never">
      <template #header>
        <div class="head">
          <div>
            <span class="card-title">摄像头墙</span>
            <span class="muted">{{ cameras.length }} 个教室 · {{ activeCount }} 个正在直播</span>
          </div>
          <div class="right">
            <el-tag v-if="activeCount > 0" type="success" effect="dark">
              <el-icon><VideoCamera /></el-icon>
              {{ activeCount }} 路实时识别中
            </el-tag>
            <el-button :icon="Refresh" @click="load">刷新</el-button>
          </div>
        </div>
      </template>

      <el-empty v-if="!cameras.length" description="暂无摄像头 · 请在系统管理中添加或运行 seed 脚本" />

      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="cam in cameras" :key="cam.id">
          <el-card shadow="hover" class="cam-card" @click="enter(cam)">
            <div class="preview">
              <div class="preview-bg">
                <el-icon :size="56" color="#94a3b8"><VideoCamera /></el-icon>
              </div>
              <el-tag
                v-if="isRunning(cam.id)"
                type="danger"
                effect="dark"
                size="small"
                class="live-badge"
              >
                ● LIVE
              </el-tag>
              <el-tag
                v-else
                :type="cam.status === 'online' ? 'success' : 'info'"
                effect="dark"
                size="small"
                class="live-badge"
              >
                {{ cam.status === 'online' ? '在线' : '离线' }}
              </el-tag>
            </div>
            <div class="info">
              <div class="name">{{ cam.name }}</div>
              <div class="meta">{{ cam.class_name || '未绑定班级' }}</div>
              <div class="actions" @click.stop>
                <el-button text type="primary" size="small" @click="enter(cam)">实时查看</el-button>
                <el-button
                  v-if="userStore.isAdmin"
                  text
                  :type="isRunning(cam.id) ? 'danger' : 'success'"
                  size="small"
                  @click="toggleLive(cam)"
                >
                  {{ isRunning(cam.id) ? '停止分析' : '开启分析' }}
                </el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, VideoCamera } from '@element-plus/icons-vue'

import {
  listActiveSessions,
  listCameras,
  manualStartLive,
  manualStopLive,
  type Camera,
  type LiveSession,
} from '@/api/m10'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const cameras = ref<Camera[]>([])
const activeSessions = ref<LiveSession[]>([])
let timer: any

const activeCount = computed(() => activeSessions.value.length)

function isRunning(cameraId: number): boolean {
  return activeSessions.value.some((s) => s.camera_id === cameraId)
}

function activeSessionId(cameraId: number): number | null {
  const s = activeSessions.value.find((s) => s.camera_id === cameraId)
  return s?.id || null
}

async function load() {
  const [cams, sessions] = await Promise.all([listCameras(), listActiveSessions()])
  cameras.value = cams.items
  activeSessions.value = sessions.items
}

async function toggleLive(cam: Camera) {
  if (isRunning(cam.id)) {
    const sid = activeSessionId(cam.id)
    if (sid) {
      await manualStopLive(sid)
      ElMessage.success('已停止')
    }
  } else {
    await manualStartLive(cam.id)
    ElMessage.success('已启动实时分析')
  }
  await load()
}

function enter(cam: Camera) {
  router.push(`/classroom/live/${cam.id}`)
}

onMounted(() => {
  load()
  timer = setInterval(load, 10000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style lang="scss" scoped>
.wall-page {
  padding-bottom: 16px;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .card-title {
    font-weight: 600;
    margin-right: 8px;
  }
  .muted {
    color: #94a3b8;
    font-size: 12px;
  }
  .right {
    display: flex;
    gap: 8px;
    align-items: center;
  }
}
.cam-card {
  margin-bottom: 16px;
  cursor: pointer;
  border-radius: 10px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  }
  :deep(.el-card__body) {
    padding: 0;
  }
}
.preview {
  position: relative;
  aspect-ratio: 16 / 9;
  background: linear-gradient(135deg, #0f172a, #1e293b);
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-bg {
  color: #94a3b8;
}
.live-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  animation: blink 1.5s infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
.info {
  padding: 10px 14px;
  .name {
    font-weight: 600;
    color: #0f172a;
  }
  .meta {
    margin-top: 4px;
    color: #94a3b8;
    font-size: 12px;
  }
  .actions {
    margin-top: 8px;
    display: flex;
    justify-content: flex-end;
    gap: 6px;
  }
}
</style>
