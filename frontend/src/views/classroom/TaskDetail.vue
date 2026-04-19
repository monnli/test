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

    <el-card shadow="never" v-if="report?.video?.url">
      <template #header><span class="card-title">视频回放</span></template>
      <video :src="resolveUrl(report.video.url)" controls class="video-player" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'

import { getTaskReport, type TaskReport } from '@/api/classroom'

const route = useRoute()
const taskId = computed(() => Number(route.params.taskId))
const report = ref<TaskReport | null>(null)
const behaviorChartRef = ref<HTMLDivElement>()
const emotionPieRef = ref<HTMLDivElement>()
const emotionLineRef = ref<HTMLDivElement>()
let bChart: echarts.ECharts | null = null
let pChart: echarts.ECharts | null = null
let lChart: echarts.ECharts | null = null
let timer: any = null

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

function resolveUrl(url: string): string {
  if (url.startsWith('http')) return url
  return url
}

const metricCards = computed(() => {
  const m = report.value?.metrics
  return [
    { label: '人体检测总数', value: m?.total_person_detections ?? 0, unit: '次', color: '#0ea5e9', desc: '所有帧累计' },
    { label: '举手次数', value: m?.hand_up_count ?? 0, unit: '', color: '#22c55e', desc: '互动指标' },
    { label: '玩手机检测', value: m?.phone_count ?? 0, unit: '', color: '#ef4444', desc: '需关注' },
    { label: '综合参与度', value: m?.engagement_score ?? 0, unit: '分', color: '#a855f7', desc: '0~100' },
  ]
})

async function load() {
  report.value = await getTaskReport(taskId.value)
  renderCharts()
  if (report.value.task.status === 'running' || report.value.task.status === 'pending') {
    timer = setTimeout(load, 2000)
  }
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
  bChart?.dispose()
  pChart?.dispose()
  lChart?.dispose()
  window.removeEventListener('resize', onResize)
})

watch(taskId, () => load())
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
.video-player {
  width: 100%;
  max-height: 480px;
  background: #000;
  border-radius: 6px;
}
</style>
