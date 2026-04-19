<template>
  <div class="dashboard" ref="rootRef">
    <header class="topbar">
      <div class="left">
        <span class="dot" />
        <span class="time">{{ now }}</span>
      </div>
      <div class="title">青苗守护者 · 校园心理健康综合数据大屏</div>
      <div class="right">
        <el-tag effect="dark" type="success" round>系统运行中</el-tag>
        <el-button text style="color:#94a3b8" @click="toggleFullscreen">
          <el-icon><FullScreen /></el-icon>
          {{ isFullscreen ? '退出全屏' : '全屏' }}
        </el-button>
        <el-button text style="color:#94a3b8" @click="$router.push('/workbench')">
          <el-icon><Back /></el-icon>返回
        </el-button>
      </div>
    </header>

    <!-- 主区：CSS Grid 严格控制高度 -->
    <main class="grid">
      <!-- 顶部 8 项指标 -->
      <section class="row stat-row">
        <div v-for="s in stats" :key="s.label" class="stat-card">
          <div class="label">{{ s.label }}</div>
          <div class="value" :style="{ color: s.color }">
            <span class="num">{{ s.value }}</span>
            <span class="unit">{{ s.unit }}</span>
          </div>
        </div>
      </section>

      <!-- 主区三列 -->
      <section class="row main-row">
        <!-- 左列 -->
        <div class="col">
          <div class="panel"><div class="panel-title">预警等级分布</div>
            <div ref="pie1Ref" class="chart" /></div>
          <div class="panel"><div class="panel-title">班级活力指数 TOP 8</div>
            <div ref="bar1Ref" class="chart" /></div>
        </div>
        <!-- 中列 -->
        <div class="col mid">
          <div class="panel hero">
            <div class="hero-bg" />
            <div class="hero-content">
              <div class="hero-num" :style="{ color: indexColor }">
                {{ data?.overview.psy_index.toFixed(1) || 0 }}
              </div>
              <div class="hero-label">校园综合心理健康指数</div>
              <div class="hero-trend">
                近 30 天平均（基于 {{ data?.overview.student_count || 0 }} 名学生 · 多源数据聚合）
              </div>
            </div>
          </div>
          <div class="panel"><div class="panel-title">近 30 天情绪健康指数曲线</div>
            <div ref="lineRef" class="chart" /></div>
        </div>
        <!-- 右列 -->
        <div class="col">
          <div class="panel"><div class="panel-title">今日课堂行为分布</div>
            <div ref="pie2Ref" class="chart" /></div>
          <div class="panel"><div class="panel-title">今日表情识别分布</div>
            <div ref="rose1Ref" class="chart" /></div>
        </div>
      </section>

      <!-- 底部两列 -->
      <section class="row bottom-row">
        <div class="panel">
          <div class="panel-title">实时预警动态</div>
          <div class="alert-stream">
            <div v-for="a in data?.recent_alerts || []" :key="a.id" class="alert-item">
              <span class="time">{{ a.created_at }}</span>
              <el-tag :type="levelTag(a.level)" effect="dark" size="small">
                {{ levelLabel(a.level) }}
              </el-tag>
              <strong>{{ a.student_name }}</strong>
              <span class="reason">{{ a.first_reason }}</span>
              <span class="score" :style="{ color: levelColor(a.level) }">
                {{ a.score.toFixed(0) }}分
              </span>
            </div>
            <div v-if="!data?.recent_alerts?.length" class="empty">暂无预警 · 一切平安</div>
          </div>
        </div>
        <div class="panel">
          <div class="panel-title">高风险学生 TOP 10</div>
          <div class="risk-list">
            <div v-for="r in data?.top_risk || []" :key="r.student_id" class="risk-row">
              <el-tag :type="levelTag(r.level)" effect="dark" size="small">
                {{ levelLabel(r.level) }}
              </el-tag>
              <strong :style="{ color: levelColor(r.level), width: '40px' }">{{ r.score }}</strong>
              <span class="name">{{ r.student_name }}</span>
              <el-button text style="color:#0ea5e9" size="small"
                @click="$router.push(`/psychology/student/${r.student_id}`)">
                档案
              </el-button>
            </div>
            <div v-if="!data?.top_risk?.length" class="empty">暂无高风险学生</div>
          </div>
        </div>
      </section>
    </main>

    <footer class="footer">
      负责任的 AI · 守护每一株青苗 · 全国大学生计算机设计大赛人工智能应用赛道作品
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { Back, FullScreen } from '@element-plus/icons-vue'

import { getDashboardAll, type DashboardAll } from '@/api/dashboard'

const data = ref<DashboardAll | null>(null)
const now = ref('')
const rootRef = ref<HTMLDivElement>()
const isFullscreen = ref(false)
let timer: any
let refreshTimer: any

const pie1Ref = ref<HTMLDivElement>()
const bar1Ref = ref<HTMLDivElement>()
const lineRef = ref<HTMLDivElement>()
const pie2Ref = ref<HTMLDivElement>()
const rose1Ref = ref<HTMLDivElement>()
let pie1: echarts.ECharts | null = null
let bar1: echarts.ECharts | null = null
let line: echarts.ECharts | null = null
let pie2: echarts.ECharts | null = null
let rose1: echarts.ECharts | null = null

const stats = computed(() => {
  const o = data.value?.overview
  return [
    { label: '在校学生', value: o?.student_count ?? 0, unit: '人', color: '#22d3ee' },
    { label: '教师', value: o?.teacher_count ?? 0, unit: '人', color: '#a78bfa' },
    { label: '班级', value: o?.class_count ?? 0, unit: '个', color: '#34d399' },
    { label: '今日新增预警', value: o?.today_alerts ?? 0, unit: '条', color: '#f59e0b' },
    { label: '待处理预警', value: o?.open_alerts ?? 0, unit: '条', color: '#ef4444' },
    { label: '本周分析视频', value: o?.week_videos ?? 0, unit: '段', color: '#0ea5e9' },
    { label: '本周量表测评', value: o?.week_assessments ?? 0, unit: '份', color: '#22c55e' },
    { label: '心理指数', value: o?.psy_index?.toFixed(0) ?? 0, unit: '/100', color: '#facc15' },
  ]
})

const indexColor = computed(() => {
  const s = data.value?.overview.psy_index || 80
  if (s >= 80) return '#22c55e'
  if (s >= 65) return '#0ea5e9'
  if (s >= 50) return '#f59e0b'
  return '#ef4444'
})

function levelTag(l: string): any {
  return { red: 'danger', orange: 'warning', yellow: 'warning', green: 'success' }[l] || 'info'
}
function levelLabel(l: string) {
  return { red: '紧急', orange: '重点', yellow: '关注', green: '正常' }[l] || l
}
function levelColor(l: string) {
  return { red: '#ef4444', orange: '#f97316', yellow: '#f59e0b', green: '#22c55e' }[l] || '#94a3b8'
}

function tickClock() {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  now.value = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

async function load() {
  data.value = await getDashboardAll()
  await nextTick()
  render()
  setTimeout(onResize, 50) // 数据加载后再做一次 resize，确保 ECharts 准确布局
}

const COLORS = ['#22d3ee', '#a78bfa', '#34d399', '#f59e0b', '#ef4444', '#0ea5e9', '#facc15', '#22c55e']

function darkAxis() {
  return {
    axisLine: { lineStyle: { color: 'rgba(148,163,184,0.3)' } },
    axisLabel: { color: '#94a3b8' },
    splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } },
  }
}

function render() {
  if (!data.value) return
  if (pie1Ref.value) {
    pie1?.dispose()
    pie1 = echarts.init(pie1Ref.value, 'dark')
    const map = data.value.alert_distribution.by_level
    pie1.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: '#94a3b8' } },
      series: [{
        type: 'pie',
        radius: ['38%', '68%'],
        center: ['50%', '45%'],
        data: [
          { name: '紧急', value: map.red || 0, itemStyle: { color: '#ef4444' } },
          { name: '重点', value: map.orange || 0, itemStyle: { color: '#f97316' } },
          { name: '关注', value: map.yellow || 0, itemStyle: { color: '#f59e0b' } },
          { name: '正常', value: map.green || 0, itemStyle: { color: '#22c55e' } },
        ],
        label: { color: '#cbd5e1' },
      }],
    })
  }

  if (bar1Ref.value) {
    bar1?.dispose()
    bar1 = echarts.init(bar1Ref.value, 'dark')
    const items = data.value.class_engagement
    bar1.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { left: 10, right: 30, top: 6, bottom: 6, containLabel: true },
      xAxis: { type: 'value', min: 0, max: 100, ...darkAxis() },
      yAxis: { type: 'category', data: items.map((c) => c.class_name), ...darkAxis() },
      series: [{
        type: 'bar',
        data: items.map((c) => ({
          value: c.engagement,
          itemStyle: { color: c.engagement >= 75 ? '#22c55e' : c.engagement >= 60 ? '#0ea5e9' : '#f59e0b' },
        })),
        barWidth: 12,
        label: { show: true, position: 'right', color: '#cbd5e1' },
      }],
    })
  }

  if (lineRef.value) {
    line?.dispose()
    line = echarts.init(lineRef.value, 'dark')
    const tl = data.value.emotion_30d
    line.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { left: 10, right: 16, top: 10, bottom: 6, containLabel: true },
      xAxis: { type: 'category', data: tl.map((p) => p.date), ...darkAxis() },
      yAxis: { type: 'value', min: 0, max: 100, ...darkAxis() },
      series: [{
        type: 'line',
        smooth: true,
        symbol: 'circle',
        data: tl.map((p) => p.score),
        lineStyle: { color: '#22d3ee', width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(34,211,238,0.4)' },
            { offset: 1, color: 'rgba(34,211,238,0.02)' },
          ]),
        },
      }],
    })
  }

  if (pie2Ref.value) {
    pie2?.dispose()
    pie2 = echarts.init(pie2Ref.value, 'dark')
    pie2.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: '#94a3b8' }, type: 'scroll' },
      series: [{
        type: 'pie',
        radius: ['38%', '68%'],
        center: ['50%', '45%'],
        data: data.value.behavior_today.items.map((d, i) => ({
          ...d,
          itemStyle: { color: COLORS[i % COLORS.length] },
        })),
        label: { color: '#cbd5e1' },
      }],
    })
  }

  if (rose1Ref.value) {
    rose1?.dispose()
    rose1 = echarts.init(rose1Ref.value, 'dark')
    rose1.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: '#94a3b8' }, type: 'scroll' },
      series: [{
        type: 'pie',
        radius: [16, 70],
        center: ['50%', '45%'],
        roseType: 'area',
        data: data.value.emotion_today.items.map((d, i) => ({
          ...d,
          itemStyle: { color: COLORS[i % COLORS.length] },
        })),
        label: { color: '#cbd5e1' },
      }],
    })
  }
}

const onResize = () => {
  pie1?.resize(); bar1?.resize(); line?.resize(); pie2?.resize(); rose1?.resize()
}

async function toggleFullscreen() {
  try {
    if (!document.fullscreenElement) {
      await rootRef.value?.requestFullscreen()
    } else {
      await document.exitFullscreen()
    }
  } catch (e) {
    // ignore
  }
}

function onFsChange() {
  isFullscreen.value = !!document.fullscreenElement
  setTimeout(onResize, 200)
}

onMounted(() => {
  tickClock()
  timer = setInterval(tickClock, 1000)
  load()
  refreshTimer = setInterval(load, 15000)
  window.addEventListener('resize', onResize)
  document.addEventListener('fullscreenchange', onFsChange)

  // 尝试自动进入浏览器全屏（多数浏览器要求用户手势触发，失败时静默）
  setTimeout(() => {
    if (!document.fullscreenElement) {
      rootRef.value?.requestFullscreen?.().catch(() => {})
    }
  }, 300)
})

onBeforeUnmount(() => {
  clearInterval(timer)
  clearInterval(refreshTimer)
  pie1?.dispose(); bar1?.dispose(); line?.dispose(); pie2?.dispose(); rose1?.dispose()
  window.removeEventListener('resize', onResize)
  document.removeEventListener('fullscreenchange', onFsChange)
  if (document.fullscreenElement) {
    document.exitFullscreen().catch(() => {})
  }
})
</script>

<style lang="scss" scoped>
/* ============== 容器 ============== */
.dashboard {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at top, #0b1224 0%, #020617 70%);
  color: #cbd5e1;
  z-index: 9999;
  font-family: -apple-system, "PingFang SC", sans-serif;
  overflow: hidden;

  /* CSS Grid：顶栏 / 主区 / 底栏 三段 */
  display: grid;
  grid-template-rows: 52px 1fr 28px;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(14, 165, 233, 0.06) 1px, transparent 1px),
      linear-gradient(90deg, rgba(14, 165, 233, 0.06) 1px, transparent 1px);
    background-size: 56px 56px;
    pointer-events: none;
    z-index: 0;
  }
}

.topbar,
.grid,
.footer {
  position: relative;
  z-index: 1;
}

/* ============== 顶栏 ============== */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid rgba(14, 165, 233, 0.15);
  .left, .right {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;
    color: #94a3b8;
    font-size: 13px;
  }
  .right { justify-content: flex-end; }
  .dot {
    width: 8px; height: 8px;
    background: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 8px #22c55e;
    animation: pulse 1.5s infinite;
  }
  .title {
    font-size: 24px;
    font-weight: 800;
    background: linear-gradient(90deg, #22d3ee, #a78bfa, #22c55e);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    letter-spacing: 4px;
    text-align: center;
    flex: 2;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ============== 主区 Grid ============== */
.grid {
  display: grid;
  /* 三行：指标卡 / 主区 / 底部 */
  grid-template-rows: auto 1.4fr 1fr;
  gap: 12px;
  padding: 12px 16px;
  min-height: 0;
  overflow: hidden;
}

.row {
  display: grid;
  gap: 12px;
  min-height: 0;
}

.stat-row {
  grid-template-columns: repeat(8, 1fr);
}

.main-row {
  grid-template-columns: 1fr 1.4fr 1fr;
}

.bottom-row {
  grid-template-columns: 1fr 1fr;
}

.col {
  display: grid;
  grid-template-rows: 1fr 1fr;
  gap: 12px;
  min-height: 0;
}

.col.mid {
  /* 中列：hero 占 32%，曲线占剩余 68%，让曲线足够大 */
  grid-template-rows: 32% 1fr;
}

/* ============== 卡片 / 面板 ============== */
.stat-card {
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 8px;
  padding: 8px 6px;
  text-align: center;
  background: linear-gradient(180deg, rgba(14, 165, 233, 0.06), rgba(14, 165, 233, 0.01));
  .label { color: #94a3b8; font-size: 12px; }
  .value {
    margin-top: 4px;
    .num { font-size: 22px; font-weight: 800; letter-spacing: 1px; }
    .unit { font-size: 11px; color: #94a3b8; margin-left: 4px; }
  }
}

.panel {
  position: relative;
  background: rgba(14, 165, 233, 0.04);
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 8px;
  padding: 8px 12px 10px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  &::before, &::after {
    content: '';
    position: absolute;
    width: 12px;
    height: 12px;
  }
  &::before {
    top: -1px; left: -1px;
    border-top: 2px solid #22d3ee;
    border-left: 2px solid #22d3ee;
  }
  &::after {
    bottom: -1px; right: -1px;
    border-bottom: 2px solid #22d3ee;
    border-right: 2px solid #22d3ee;
  }
}

.panel-title {
  flex-shrink: 0;
  color: #f1f5f9;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 1px;
  padding-bottom: 6px;
  margin-bottom: 4px;
  border-bottom: 1px dashed rgba(14, 165, 233, 0.2);
}

.chart {
  flex: 1;
  min-height: 0;
  width: 100%;
}

/* ============== Hero 巨型指数 ============== */
.panel.hero {
  text-align: center;
  padding: 12px;
  position: relative;
  overflow: hidden;
  .hero-bg {
    position: absolute;
    inset: -10%;
    background: radial-gradient(circle, rgba(34,211,238,0.18) 0%, transparent 60%);
    animation: rotate 16s linear infinite;
  }
  .hero-content {
    position: relative;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  .hero-num {
    font-size: 64px;
    font-weight: 900;
    letter-spacing: 4px;
    line-height: 1;
    text-shadow: 0 0 30px currentColor;
  }
  .hero-label {
    margin-top: 8px;
    color: #94a3b8;
    letter-spacing: 4px;
    font-size: 13px;
  }
  .hero-trend {
    margin-top: 4px;
    color: #64748b;
    font-size: 12px;
  }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ============== 预警流 ============== */
.alert-stream {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 4px;
  .alert-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 4px;
    border-left: 3px solid #0ea5e9;
    flex-shrink: 0;
    .time { color: #64748b; font-size: 12px; min-width: 50px; }
    .reason {
      flex: 1;
      color: #94a3b8;
      font-size: 12px;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }
    .score { font-weight: 700; }
  }
  .empty { color: #94a3b8; text-align: center; padding: 40px 0; }
}

/* ============== 风险列表（替代 el-table） ============== */
.risk-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding-right: 4px;
  .risk-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 10px;
    border-bottom: 1px solid rgba(14, 165, 233, 0.06);
    flex-shrink: 0;
    &:nth-child(even) { background: rgba(14, 165, 233, 0.03); }
    .name { flex: 1; color: #cbd5e1; }
  }
  .empty { color: #94a3b8; text-align: center; padding: 40px 0; }
}

.footer {
  text-align: center;
  color: #64748b;
  font-size: 11px;
  letter-spacing: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
