<template>
  <div class="task-detail">
    <el-card shadow="never">
      <template #header>
        <div class="head">
          <span class="title">分析任务 #{{ taskId }}</span>
          <el-tag :type="statusTag(report?.task.status)" effect="dark">
            {{ statusLabel(report?.task.status) }}
          </el-tag>
        </div>
      </template>
      <el-progress :percentage="report?.task.progress || 0" :status="progressStatus" />
      <div class="meta">
        <span>已处理 {{ report?.task.processed_frames || 0 }} / {{ report?.task.total_frames || 0 }} 帧</span>
        <span>抽帧间隔 {{ report?.task.sample_interval_sec || '—' }}s</span>
        <span>开始 {{ report?.task.started_at || '—' }}</span>
        <span>完成 {{ report?.task.finished_at || '—' }}</span>
      </div>
    </el-card>

    <el-row :gutter="16" class="metrics-row" v-if="report">
      <el-col :xs="12" :md="6" v-for="m in metricCards" :key="m.label">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-label">{{ m.label }}</div>
          <div class="metric-value" :style="{ color: m.color }">
            {{ m.value }}<span class="unit">{{ m.unit }}</span>
          </div>
          <div class="metric-desc">{{ m.desc }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" v-if="report">
      <el-col :xs="24" :md="14">
        <el-card shadow="never">
          <template #header><span class="card-title">课堂行为时间轴</span></template>
          <div ref="behaviorChartRef" class="chart" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="10">
        <el-card shadow="never">
          <template #header><span class="card-title">情绪分布</span></template>
          <div ref="emotionPieRef" class="chart" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" v-if="report">
      <template #header><span class="card-title">情绪曲线（5 秒聚合）</span></template>
      <div ref="emotionLineRef" class="chart" />
    </el-card>

    <el-card shadow="never" v-if="report?.metrics?.behavior_by_class">
      <template #header><span class="card-title">课堂行为八类统计</span></template>
      <div class="behavior-tags">
        <el-tag v-for="row in behaviorClassRows" :key="row.name" type="info" effect="plain" class="btag">
          {{ row.name }} · {{ row.count }}
        </el-tag>
      </div>
    </el-card>

    <el-card shadow="never" v-if="report?.video?.url">
      <template #header>
        <div class="video-head">
          <span class="card-title">视频回放</span>
          <el-tag size="small" :type="inferring ? 'warning' : 'success'">
            {{ inferring ? 'YOLO 识别中…' : '实时框图已开启' }}
          </el-tag>
        </div>
      </template>
      <div class="video-stage">
        <video
          ref="videoRef"
          :src="resolveMediaUrl(report.video.url)"
          controls
          playsinline
          crossorigin="anonymous"
          class="video-player"
          @loadedmetadata="onVideoMeta"
          @play="onVideoPlay"
          @pause="onVideoPause"
          @timeupdate="onVideoTime"
        />
        <canvas ref="overlayRef" class="video-overlay" />
      </div>
      <p class="video-hint">
        播放时约每 {{ liveIntervalMs }}ms 将当前帧送后端 YOLO 识别，绿框与标签叠加在画面上；暂停时不请求。CPU 环境可能略有延迟。
      </p>
      <p v-if="liveError" class="live-err">{{ liveError }}</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'

import {
  detectVideoFrame,
  getTaskReport,
  type BehaviorDetection,
  type TaskReport,
} from '@/api/classroom'
import { resolveMediaUrl } from '@/utils/mediaUrl'

const route = useRoute()
const taskId = computed(() => Number(route.params.taskId))
const report = ref<TaskReport | null>(null)
const behaviorChartRef = ref<HTMLDivElement>()
const emotionPieRef = ref<HTMLDivElement>()
const emotionLineRef = ref<HTMLDivElement>()
const videoRef = ref<HTMLVideoElement | null>(null)
const overlayRef = ref<HTMLCanvasElement | null>(null)
let bChart: echarts.ECharts | null = null
let pChart: echarts.ECharts | null = null
let lChart: echarts.ECharts | null = null
let timer: any = null

const liveIntervalMs = 500
const inferring = ref(false)
const liveError = ref('')
const lastDetections = ref<BehaviorDetection[]>([])
let playing = false
let lastInferAt = 0
let tickId = 0
let rafId = 0
let abortCtl: AbortController | null = null
let attachedLiveVideoId = 0

const progressStatus = computed(() => {
  const s = report.value?.task.status
  if (s === 'success') return 'success'
  if (s === 'failed') return 'exception'
  return ''
})

function statusTag(s?: string): any {
  return { pending: 'info', running: 'warning', success: 'success', failed: 'danger' }[s || ''] || 'info'
}
function statusLabel(s?: string) {
  return { pending: '排队中', running: '运行中', success: '已完成', failed: '失败' }[s || ''] || '未知'
}

const BEHAVIOR_EIGHT = [
  '低头写字',
  '低头看书',
  '抬头听课',
  '转头',
  '举手',
  '站立',
  '小组讨论',
  '教师指导',
] as const

const behaviorClassRows = computed(() => {
  const raw = report.value?.metrics?.behavior_by_class
  if (!raw) return []
  return BEHAVIOR_EIGHT.map((name) => ({ name, count: raw[name] ?? 0 }))
})

const metricCards = computed(() => {
  const m = report.value?.metrics
  return [
    {
      label: '抬头听课 + 站立',
      value: m?.total_person_detections ?? 0,
      unit: '次',
      color: '#0ea5e9',
      desc: '在场/体态线索',
    },
    { label: '举手次数', value: m?.hand_up_count ?? 0, unit: '', color: '#22c55e', desc: '互动' },
    {
      label: '低头写字 + 低头看书',
      value: m?.phone_count ?? 0,
      unit: '',
      color: '#f59e0b',
      desc: '低头类行为',
    },
    { label: '综合参与度', value: m?.engagement_score ?? 0, unit: '分', color: '#a855f7', desc: '0~100' },
  ]
})

async function load() {
  report.value = await getTaskReport(taskId.value)
  renderCharts()
  if (report.value.task.status === 'running' || report.value.task.status === 'pending') {
    timer = setTimeout(load, 2000)
  }
  await nextTick()
  void setupLiveOverlay()
}

function tearDownLiveOverlay() {
  playing = false
  lastInferAt = 0
  clearTimeout(tickId)
  tickId = 0
  cancelAnimationFrame(rafId)
  abortCtl?.abort()
  abortCtl = null
  window.removeEventListener('resize', scheduleDrawOverlay)
}

function scheduleDrawOverlay() {
  cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(drawOverlay)
}

function drawOverlay() {
  const v = videoRef.value
  const c = overlayRef.value
  if (!v || !c) return
  const dets = lastDetections.value
  const vw = v.videoWidth
  const vh = v.videoHeight
  if (!vw || !vh) return

  const rw = v.clientWidth
  const rh = v.clientHeight
  const scale = Math.min(rw / vw, rh / vh)
  const dw = vw * scale
  const dh = vh * scale
  const ox = (rw - dw) / 2
  const oy = (rh - dh) / 2

  const pr = window.devicePixelRatio || 1
  c.width = Math.max(1, Math.floor(rw * pr))
  c.height = Math.max(1, Math.floor(rh * pr))
  const ctx = c.getContext('2d')
  if (!ctx) return
  ctx.setTransform(pr, 0, 0, pr, 0, 0)
  ctx.clearRect(0, 0, rw, rh)
  ctx.lineWidth = 2
  ctx.font = '12px sans-serif'
  for (const det of dets) {
    const [x1, y1, x2, y2] = det.bbox
    const sx1 = ox + x1 * scale
    const sy1 = oy + y1 * scale
    const sx2 = ox + x2 * scale
    const sy2 = oy + y2 * scale
    ctx.strokeStyle = '#22c55e'
    ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1)
    const text = `${det.label_cn} ${(det.confidence * 100).toFixed(0)}%`
    ctx.fillStyle = 'rgba(0,0,0,0.55)'
    ctx.fillRect(sx1, Math.max(0, sy1 - 18), Math.min(rw - sx1, text.length * 7 + 10), 18)
    ctx.fillStyle = '#fff'
    ctx.fillText(text, sx1 + 4, sy1 - 4)
  }
}

function onVideoMeta() {
  scheduleDrawOverlay()
}

function onVideoPlay() {
  playing = true
  lastInferAt = 0
}

function onVideoPause() {
  playing = false
}

function onVideoTime() {
  scheduleDrawOverlay()
}

async function runLiveInfer() {
  const v = videoRef.value
  const vid = report.value?.video?.id
  if (!v || !vid || v.readyState < 2) return
  if (!playing || v.paused) return
  const now = performance.now()
  if (now - lastInferAt < liveIntervalMs || inferring.value) return
  lastInferAt = now

  const vw = v.videoWidth
  const vh = v.videoHeight
  if (!vw || !vh) return

  const cap = document.createElement('canvas')
  cap.width = vw
  cap.height = vh
  const cx = cap.getContext('2d')
  if (!cx) return
  cx.drawImage(v, 0, 0, vw, vh)

  const blob: Blob | null = await new Promise((res) =>
    cap.toBlob((b) => res(b), 'image/jpeg', 0.85),
  )
  if (!blob) return

  inferring.value = true
  liveError.value = ''
  abortCtl?.abort()
  abortCtl = new AbortController()
  try {
    const data = await detectVideoFrame(vid, blob, v.currentTime, 0.35, abortCtl.signal)
    if (data._error) liveError.value = String(data._error)
    lastDetections.value = data.detections || []
    scheduleDrawOverlay()
  } catch (e: any) {
    if (e?.code === 'ERR_CANCELED' || e?.name === 'CanceledError' || e?.message === 'canceled') return
    liveError.value = e?.message || '识别失败'
  } finally {
    inferring.value = false
  }
}

function liveTickLoop() {
  tickId = window.setTimeout(() => {
    void runLiveInfer()
    liveTickLoop()
  }, liveIntervalMs)
}

async function setupLiveOverlay() {
  const vid = report.value?.video?.id
  const url = report.value?.video?.url
  if (!vid || !url) return
  if (attachedLiveVideoId === vid) {
    await nextTick()
    if (videoRef.value) return
  }
  tearDownLiveOverlay()
  attachedLiveVideoId = vid
  await nextTick()
  if (!videoRef.value) {
    attachedLiveVideoId = 0
    return
  }
  window.addEventListener('resize', scheduleDrawOverlay)
  liveTickLoop()
}

function renderCharts() {
  if (!report.value) return
  const bt = report.value.behavior_timeline || []
  const et = report.value.emotion_timeline || []

  const bKeys = Array.from(new Set(bt.flatMap((p) => Object.keys(p).filter((k) => k !== 'time'))))
  const eKeys = Array.from(new Set(et.flatMap((p) => Object.keys(p).filter((k) => k !== 'time'))))

  if (behaviorChartRef.value) {
    bChart?.dispose()
    bChart = echarts.init(behaviorChartRef.value)
    bChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: bKeys, type: 'scroll', bottom: 0 },
      grid: { left: 40, right: 16, top: 24, bottom: 50 },
      xAxis: { type: 'category', data: bt.map((p) => `${p.time}s`) },
      yAxis: { type: 'value', name: '次数' },
      series: bKeys.map((k) => ({
        name: k,
        type: 'bar',
        stack: 'b',
        data: bt.map((p) => p[k] || 0),
      })),
      color: ['#0ea5e9', '#22c55e', '#a855f7', '#ef4444', '#f59e0b', '#14b8a6'],
    })
  }

  if (emotionPieRef.value) {
    pChart?.dispose()
    pChart = echarts.init(emotionPieRef.value)
    const totals: Record<string, number> = {}
    et.forEach((p) => {
      eKeys.forEach((k) => {
        totals[k] = (totals[k] || 0) + (p[k] || 0)
      })
    })
    pChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, type: 'scroll' },
      series: [
        {
          type: 'pie',
          radius: ['30%', '70%'],
          data: Object.entries(totals).map(([name, value]) => ({ name, value })),
          itemStyle: { borderRadius: 6 },
        },
      ],
      color: ['#22c55e', '#0ea5e9', '#a855f7', '#f59e0b', '#ef4444', '#14b8a6', '#94a3b8'],
    })
  }

  if (emotionLineRef.value) {
    lChart?.dispose()
    lChart = echarts.init(emotionLineRef.value)
    lChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: eKeys, type: 'scroll', bottom: 0 },
      grid: { left: 40, right: 16, top: 24, bottom: 50 },
      xAxis: { type: 'category', data: et.map((p) => `${p.time}s`) },
      yAxis: { type: 'value', name: '次数' },
      series: eKeys.map((k) => ({
        name: k,
        type: 'line',
        smooth: true,
        data: et.map((p) => p[k] || 0),
      })),
      color: ['#22c55e', '#0ea5e9', '#a855f7', '#f59e0b', '#ef4444', '#14b8a6', '#94a3b8'],
    })
  }
}

const onResize = () => {
  bChart?.resize()
  pChart?.resize()
  lChart?.resize()
}

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  if (timer) clearTimeout(timer)
  tearDownLiveOverlay()
  bChart?.dispose()
  pChart?.dispose()
  lChart?.dispose()
  window.removeEventListener('resize', onResize)
})

watch(taskId, () => {
  attachedLiveVideoId = 0
  tearDownLiveOverlay()
  lastDetections.value = []
  liveError.value = ''
  void load()
})
</script>

<style lang="scss" scoped>
.task-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .title {
    font-weight: 600;
  }
}
.meta {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  color: #64748b;
  font-size: 12px;
}
.metrics-row {
  margin-top: 0;
}
.metric-card {
  border-radius: 10px;
  .metric-label {
    color: #64748b;
    font-size: 12px;
  }
  .metric-value {
    margin-top: 4px;
    font-size: 26px;
    font-weight: 700;
    .unit {
      font-size: 12px;
      color: #94a3b8;
      margin-left: 4px;
    }
  }
  .metric-desc {
    color: #94a3b8;
    font-size: 12px;
    margin-top: 2px;
  }
}
.card-title {
  font-weight: 600;
}
.chart {
  width: 100%;
  height: 320px;
}
.video-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.video-stage {
  position: relative;
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
}
.video-player {
  display: block;
  width: 100%;
  max-height: 480px;
  object-fit: contain;
  background: #000;
  border-radius: 6px;
}
.video-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.video-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #64748b;
}
.live-err {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--el-color-danger);
}
.behavior-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.btag {
  margin: 0;
}
</style>
