<template>
  <el-card shadow="never">
    <template #header>
      <div class="head">
        <span class="card-title">实时摄像头分析</span>
        <el-tag :type="connected ? 'success' : 'info'" effect="dark" size="small">
          {{ connected ? 'WS 已连接' : '未连接' }}
        </el-tag>
      </div>
    </template>

    <div class="layout">
      <div class="video-area">
        <video ref="videoRef" autoplay muted playsinline class="video" />
        <canvas ref="canvasRef" class="overlay" />
      </div>
      <div class="panel">
        <el-form label-width="90px" size="small">
          <el-form-item label="分析频率">
            <el-input-number v-model="intervalMs" :min="500" :max="5000" :step="200" />
            <span class="hint">毫秒（越小越实时，越大越省力）</span>
          </el-form-item>
          <el-form-item>
            <el-button v-if="!started" type="primary" @click="start">开始</el-button>
            <el-button v-else type="danger" @click="stop">停止</el-button>
          </el-form-item>
        </el-form>

        <el-divider />

        <div class="result">
          <div class="row">
            <span class="label">主表情：</span>
            <el-tag v-if="lastEmotion" type="success" effect="dark">
              {{ lastEmotion.emotion_cn }} （{{ ((lastEmotion.confidence || 0) * 100).toFixed(0) }}%）
            </el-tag>
            <span v-else>—</span>
          </div>
          <div class="row">
            <span class="label">行为汇总：</span>
            <el-tag
              v-for="(c, k) in lastSummary"
              :key="k"
              effect="plain"
              class="tag"
            >{{ k }} × {{ c }}</el-tag>
            <span v-if="!Object.keys(lastSummary || {}).length">—</span>
          </div>
          <div class="row">
            <span class="label">已分析帧：</span> {{ processed }}
          </div>
        </div>
      </div>
    </div>
    <el-alert
      :closable="false"
      type="info"
      class="hint-alert"
    >
      <template #title>
        本页演示实时摄像头 → AI 分析 → 结果叠加。AI 服务在 mock 模式下也能正常工作（生成稳定的随机结果）。
      </template>
    </el-alert>
  </el-card>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { io, type Socket } from 'socket.io-client'

const wsBase = import.meta.env.VITE_WS_BASE_URL || (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host

const videoRef = ref<HTMLVideoElement>()
const canvasRef = ref<HTMLCanvasElement>()
const intervalMs = ref(1000)
const started = ref(false)
const connected = ref(false)
const lastEmotion = ref<any>(null)
const lastSummary = ref<Record<string, number>>({})
const processed = ref(0)

let stream: MediaStream | null = null
let socket: Socket | null = null
let timer: any = null

async function start() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    if (videoRef.value) {
      videoRef.value.srcObject = stream
    }
  } catch (exc: any) {
    ElMessage.error('无法访问摄像头：' + (exc?.message || exc))
    return
  }

  socket = io(`${wsBase}/ws`, { path: '/socket.io', transports: ['websocket'] })

  socket.on('connect', () => {
    connected.value = true
  })
  socket.on('disconnect', () => {
    connected.value = false
  })
  socket.on('analysis_result', (payload: any) => {
    if (payload?.behavior) {
      lastSummary.value = payload.behavior.summary || {}
      drawDetections(payload.behavior.detections || [])
    }
    if (payload?.emotion) {
      lastEmotion.value = payload.emotion
    }
    processed.value++
  })

  started.value = true
  scheduleSend()
}

function scheduleSend() {
  if (!started.value) return
  timer = setInterval(captureAndSend, intervalMs.value)
}

function captureAndSend() {
  if (!videoRef.value || !socket) return
  const v = videoRef.value
  if (!v.videoWidth) return
  const cvs = document.createElement('canvas')
  cvs.width = v.videoWidth
  cvs.height = v.videoHeight
  const ctx = cvs.getContext('2d')
  if (!ctx) return
  ctx.drawImage(v, 0, 0)
  const data = cvs.toDataURL('image/jpeg', 0.7).split(',', 2)[1]
  socket.emit('frame', { frame: data, timestamp: Date.now() })
}

function drawDetections(detections: any[]) {
  const v = videoRef.value
  const c = canvasRef.value
  if (!v || !c) return
  c.width = v.clientWidth
  c.height = v.clientHeight
  const ctx = c.getContext('2d')
  if (!ctx) return
  ctx.clearRect(0, 0, c.width, c.height)
  if (!v.videoWidth) return
  const sx = c.width / v.videoWidth
  const sy = c.height / v.videoHeight
  ctx.lineWidth = 2
  ctx.font = '12px PingFang SC, sans-serif'
  detections.forEach((d) => {
    const [x1, y1, x2, y2] = d.bbox || [0, 0, 0, 0]
    const color = d.label === 'cell phone' ? '#ef4444' : '#22c55e'
    ctx.strokeStyle = color
    ctx.fillStyle = color
    ctx.strokeRect(x1 * sx, y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy)
    const label = `${d.label_cn} ${(d.confidence * 100).toFixed(0)}%`
    ctx.fillRect(x1 * sx, Math.max(0, y1 * sy - 16), ctx.measureText(label).width + 8, 16)
    ctx.fillStyle = '#fff'
    ctx.fillText(label, x1 * sx + 4, Math.max(12, y1 * sy - 4))
  })
}

function stop() {
  if (timer) clearInterval(timer)
  timer = null
  if (stream) {
    stream.getTracks().forEach((t) => t.stop())
    stream = null
  }
  if (socket) {
    socket.disconnect()
    socket = null
  }
  started.value = false
  connected.value = false
}

onBeforeUnmount(stop)
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
.layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}
.video-area {
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
}
.video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.panel {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  .label {
    color: #64748b;
    margin-right: 6px;
  }
  .row {
    margin-bottom: 8px;
  }
  .tag {
    margin: 2px 4px 2px 0;
  }
}
.hint {
  margin-left: 8px;
  font-size: 12px;
  color: #94a3b8;
}
.hint-alert {
  margin-top: 16px;
}
</style>
