<template>
  <div class="live-page">
    <el-card shadow="never" class="header-card">
      <div class="header">
        <div>
          <h2>
            <el-icon><VideoCamera /></el-icon>
            {{ camera?.name || '摄像头' }}
          </h2>
          <div class="meta">
            {{ camera?.class_name || '' }} ·
            <el-tag :type="isRunning ? 'danger' : 'info'" effect="dark" size="small">
              {{ isRunning ? '● 实时分析中' : '未开启分析' }}
            </el-tag>
          </div>
        </div>
        <div class="actions">
          <el-button
            v-if="userStore.isAdmin"
            :type="isRunning ? 'danger' : 'primary'"
            @click="toggleLive"
          >
            {{ isRunning ? '停止实时分析' : '开启实时分析' }}
          </el-button>
          <el-button @click="$router.push('/classroom/cameras')">
            返回摄像头墙
          </el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :xs="24" :md="16">
        <el-card shadow="never">
          <template #header><span class="card-title">视频与识别结果叠加</span></template>
          <div class="stage">
            <div class="stage-bg">
              <div class="placeholder">
                <el-icon :size="80" color="#64748b"><VideoCamera /></el-icon>
                <div class="hint">
                  实时视频流（演示模式下显示模拟画面，识别结果通过 WebSocket 实时叠加）
                </div>
              </div>
            </div>
            <canvas ref="canvasRef" class="overlay" />
          </div>
          <div class="legend">
            <el-tag size="small" type="success">绿框 · 正常学生</el-tag>
            <el-tag size="small" type="warning">橙框 · 举手 / 站立</el-tag>
            <el-tag size="small" type="danger">红框 · 玩手机 / 趴桌</el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="never">
          <template #header><span class="card-title">实时指标</span></template>
          <div class="metric">
            <div class="m-label">当前在场人数</div>
            <div class="m-value">{{ lastSummary?.total_persons ?? 0 }}</div>
          </div>
          <div class="metric">
            <div class="m-label">当前参与度</div>
            <div class="m-value" :style="{ color: engagementColor }">
              {{ lastSummary?.engagement_score ?? '—' }}
            </div>
          </div>
          <el-divider>实时行为分布</el-divider>
          <div class="bhv">
            <div class="bhv-row">
              <span>抬头</span>
              <el-progress
                :percentage="pct('head_up')"
                :color="'#22c55e'"
                :stroke-width="8"
                :show-text="false"
              />
              <span class="num">{{ lastSummary?.head_up ?? 0 }}</span>
            </div>
            <div class="bhv-row">
              <span>举手</span>
              <el-progress
                :percentage="pct('hand_up', 20)"
                :color="'#0ea5e9'"
                :stroke-width="8"
                :show-text="false"
              />
              <span class="num">{{ lastSummary?.hand_up ?? 0 }}</span>
            </div>
            <div class="bhv-row">
              <span>低头</span>
              <el-progress
                :percentage="pct('head_down')"
                :color="'#f59e0b'"
                :stroke-width="8"
                :show-text="false"
              />
              <span class="num">{{ lastSummary?.head_down ?? 0 }}</span>
            </div>
            <div class="bhv-row">
              <span>玩手机</span>
              <el-progress
                :percentage="pct('using_phone')"
                :color="'#ef4444'"
                :stroke-width="8"
                :show-text="false"
              />
              <span class="num">{{ lastSummary?.using_phone ?? 0 }}</span>
            </div>
            <div class="bhv-row">
              <span>趴桌</span>
              <el-progress
                :percentage="pct('lying')"
                :color="'#a855f7'"
                :stroke-width="8"
                :show-text="false"
              />
              <span class="num">{{ lastSummary?.lying ?? 0 }}</span>
            </div>
          </div>
          <el-divider>已识别学生</el-divider>
          <div class="student-list" v-if="recognizedStudents.length">
            <el-tag
              v-for="s in recognizedStudents"
              :key="s.student_id"
              size="small"
              effect="plain"
              type="success"
              class="st-tag"
            >
              {{ s.student_name || `#${s.student_id}` }}
            </el-tag>
          </div>
          <div v-else class="empty">暂无</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { io, type Socket } from 'socket.io-client'
import { ElMessage } from 'element-plus'
import { VideoCamera } from '@element-plus/icons-vue'

import {
  getCameraStatus,
  listCameras,
  manualStartLive,
  manualStopLive,
  type Camera,
} from '@/api/m10'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
const cameraId = computed(() => Number(route.params.cameraId))
const camera = ref<Camera | null>(null)
const isRunning = ref(false)
const activeSessionId = ref<number | null>(null)
const lastSummary = ref<any>(null)
const lastStudents = ref<any[]>([])
const canvasRef = ref<HTMLCanvasElement>()
let socket: Socket | null = null
let statusTimer: any

const recognizedStudents = computed(() =>
  lastStudents.value.filter((s) => s.student_id && s.student_name).slice(0, 20),
)

const engagementColor = computed(() => {
  const v = lastSummary.value?.engagement_score ?? 0
  if (v >= 75) return '#22c55e'
  if (v >= 60) return '#0ea5e9'
  if (v >= 45) return '#f59e0b'
  return '#ef4444'
})

function pct(key: string, base = 30): number {
  const v = lastSummary.value?.[key] ?? 0
  return Math.min(100, (v / base) * 100)
}

async function load() {
  const cams = (await listCameras()).items
  camera.value = cams.find((c) => c.id === cameraId.value) || null
  await loadStatus()
}

async function loadStatus() {
  const r = await getCameraStatus(cameraId.value)
  isRunning.value = r.is_running
  activeSessionId.value = r.active_session_id
}

async function toggleLive() {
  if (isRunning.value && activeSessionId.value) {
    await manualStopLive(activeSessionId.value)
    ElMessage.success('已停止')
  } else {
    await manualStartLive(cameraId.value)
    ElMessage.success('已启动')
  }
  await loadStatus()
}

function connectWs() {
  const wsBase =
    import.meta.env.VITE_WS_BASE_URL ||
    (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host
  socket = io(`${wsBase}/ws`, { path: '/socket.io', transports: ['websocket'] })
  socket.on('live_analysis', (payload: any) => {
    if (payload?.camera_id !== cameraId.value) return
    lastSummary.value = payload.summary
    lastStudents.value = payload.students || []
    draw(payload.students || [])
  })
}

function draw(students: any[]) {
  const c = canvasRef.value
  if (!c) return
  const parent = c.parentElement as HTMLElement
  c.width = parent.clientWidth
  c.height = parent.clientHeight
  const ctx = c.getContext('2d')
  if (!ctx) return
  ctx.clearRect(0, 0, c.width, c.height)

  // 假设原画 1280x720，按比例绘制
  const sx = c.width / 1280
  const sy = c.height / 720

  ctx.lineWidth = 2
  ctx.font = '12px PingFang SC, sans-serif'

  students.forEach((s) => {
    const [x1, y1, x2, y2] = s.bbox || [0, 0, 0, 0]
    const hasBad = s.using_phone || (s.behaviors_cn || []).includes('趴桌')
    const hasAction = (s.behaviors_cn || []).includes('举手') || (s.behaviors_cn || []).includes('站立')
    const color = hasBad ? '#ef4444' : hasAction ? '#f59e0b' : '#22c55e'
    ctx.strokeStyle = color
    ctx.fillStyle = color
    ctx.strokeRect(x1 * sx, y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy)

    const label = s.student_name
      ? `${s.student_name} · ${(s.behaviors_cn || []).slice(0, 2).join('/')}`
      : `${(s.behaviors_cn || []).slice(0, 2).join('/') || '学生'}`
    const emoji = s.emotion_cn ? ` [${s.emotion_cn}]` : ''
    const full = label + emoji
    const textWidth = ctx.measureText(full).width + 8
    ctx.fillRect(x1 * sx, Math.max(0, y1 * sy - 18), textWidth, 18)
    ctx.fillStyle = '#fff'
    ctx.fillText(full, x1 * sx + 4, Math.max(14, y1 * sy - 4))
  })
}

onMounted(() => {
  load()
  connectWs()
  statusTimer = setInterval(loadStatus, 5000)
})

onBeforeUnmount(() => {
  if (socket) socket.disconnect()
  if (statusTimer) clearInterval(statusTimer)
})
</script>

<style lang="scss" scoped>
.live-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.header-card {
  border-radius: 10px;
  background: linear-gradient(135deg, #f0fdf4, #f0f9ff);
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  h2 {
    margin: 0;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .meta {
    margin-top: 6px;
    color: #64748b;
    font-size: 13px;
  }
  .actions {
    display: flex;
    gap: 8px;
  }
}
.card-title {
  font-weight: 600;
}
.stage {
  position: relative;
  aspect-ratio: 16 / 9;
  background: #020617;
  border-radius: 8px;
  overflow: hidden;
}
.stage-bg {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  .placeholder {
    text-align: center;
  }
  .hint {
    margin-top: 12px;
    font-size: 13px;
  }
}
.overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.legend {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  justify-content: center;
}
.metric {
  text-align: center;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
  &:last-of-type {
    border-bottom: none;
  }
  .m-label {
    color: #64748b;
    font-size: 12px;
  }
  .m-value {
    margin-top: 4px;
    font-size: 32px;
    font-weight: 800;
    color: #0f172a;
  }
}
.bhv {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bhv-row {
  display: flex;
  align-items: center;
  gap: 8px;
  > span:first-child {
    width: 44px;
    color: #64748b;
    font-size: 13px;
  }
  > :global(.el-progress) {
    flex: 1;
  }
  .num {
    width: 30px;
    text-align: right;
    font-weight: 600;
    color: #0f172a;
  }
}
.student-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.st-tag {
  margin: 2px;
}
.empty {
  color: #94a3b8;
  text-align: center;
  padding: 16px 0;
  font-size: 12px;
}
</style>
