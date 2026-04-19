<template>
  <div class="dashboard">
    <!-- 顶栏 -->
    <header class="topbar">
      <div class="left">
        <span class="dot" />
        <span class="time">{{ now }}</span>
      </div>
      <div class="title">青苗守护者 · 校园心理健康综合数据大屏</div>
      <div class="right">
        <el-tag effect="dark" type="success" round>系统运行中</el-tag>
        <el-button text style="color:#94a3b8" @click="$router.push('/workbench')">
          <el-icon><Back /></el-icon>返回工作台
        </el-button>
      </div>
    </header>

    <div class="grid">
      <!-- 顶部统计 -->
      <el-row :gutter="16" class="stat-row">
        <el-col :span="3" v-for="s in stats" :key="s.label">
          <div class="stat-card">
            <div class="label">{{ s.label }}</div>
            <div class="value" :style="{ color: s.color }">
              <span class="num">{{ s.value }}</span>
              <span class="unit">{{ s.unit }}</span>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="main-row">
        <!-- 左列 -->
        <el-col :span="6">
          <div class="panel">
            <div class="panel-title">预警等级分布</div>
            <div ref="pie1Ref" class="chart" />
          </div>
          <div class="panel">
            <div class="panel-title">班级活力指数 TOP 8</div>
            <div ref="bar1Ref" class="chart" />
          </div>
        </el-col>

        <!-- 中列：核心 -->
        <el-col :span="12">
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
          <div class="panel">
            <div class="panel-title">近 30 天情绪健康指数曲线</div>
            <div ref="lineRef" class="chart big" />
          </div>
        </el-col>

        <!-- 右列 -->
        <el-col :span="6">
          <div class="panel">
            <div class="panel-title">今日课堂行为分布</div>
            <div ref="pie2Ref" class="chart" />
          </div>
          <div class="panel">
            <div class="panel-title">今日表情识别分布</div>
            <div ref="rose1Ref" class="chart" />
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="bottom-row">
        <el-col :span="12">
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
        </el-col>
        <el-col :span="12">
          <div class="panel">
            <div class="panel-title">高风险学生 TOP 10</div>
            <el-table
              :data="data?.top_risk || []"
              :show-header="true"
              :row-style="() => ({ background: 'transparent', color: '#cbd5e1' })"
              :header-cell-style="{ background: 'transparent', color: '#94a3b8', borderBottom: '1px solid rgba(14,165,233,0.2)' }"
              :cell-style="{ borderBottom: '1px solid rgba(14,165,233,0.05)' }"
              style="--el-table-bg-color: transparent; background: transparent"
              stripe
            >
              <el-table-column label="级别" width="80">
                <template #default="{ row }">
                  <el-tag :type="levelTag(row.level)" effect="dark" size="small">
                    {{ levelLabel(row.level) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="评分" width="80">
                <template #default="{ row }">
                  <strong :style="{ color: levelColor(row.level) }">{{ row.score }}</strong>
                </template>
              </el-table-column>
              <el-table-column prop="student_name" label="学生" />
              <el-table-column label="" width="80">
                <template #default="{ row }">
                  <el-button text style="color:#0ea5e9" @click="$router.push(`/psychology/student/${row.student_id}`)">
                    档案
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-col>
      </el-row>
    </div>

    <footer class="footer">
      负责任的 AI · 守护每一株青苗 · 全国大学生计算机设计大赛人工智能应用赛道作品
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { Back } from '@element-plus/icons-vue'

import { getDashboardAll, type DashboardAll } from '@/api/dashboard'

const data = ref<DashboardAll | null>(null)
const now = ref('')
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
  render()
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
  // 预警等级饼图
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
        radius: ['40%', '70%'],
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

  // 班级活力柱图
  if (bar1Ref.value) {
    bar1?.dispose()
    bar1 = echarts.init(bar1Ref.value, 'dark')
    const items = data.value.class_engagement
    bar1.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { left: 80, right: 16, top: 16, bottom: 24 },
      xAxis: { type: 'value', min: 0, max: 100, ...darkAxis() },
      yAxis: {
        type: 'category',
        data: items.map((c) => c.class_name),
        ...darkAxis(),
      },
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

  // 30 天曲线
  if (lineRef.value) {
    line?.dispose()
    line = echarts.init(lineRef.value, 'dark')
    const tl = data.value.emotion_30d
    line.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 16, top: 24, bottom: 30 },
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

  // 今日行为
  if (pie2Ref.value) {
    pie2?.dispose()
    pie2 = echarts.init(pie2Ref.value, 'dark')
    pie2.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: '#94a3b8' }, type: 'scroll' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: data.value.behavior_today.items.map((d, i) => ({
          ...d,
          itemStyle: { color: COLORS[i % COLORS.length] },
        })),
        label: { color: '#cbd5e1' },
      }],
    })
  }

  // 今日情绪玫瑰
  if (rose1Ref.value) {
    rose1?.dispose()
    rose1 = echarts.init(rose1Ref.value, 'dark')
    rose1.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: '#94a3b8' }, type: 'scroll' },
      series: [{
        type: 'pie',
        radius: [20, 90],
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

onMounted(() => {
  tickClock()
  timer = setInterval(tickClock, 1000)
  load()
  refreshTimer = setInterval(load, 15000)
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  clearInterval(timer)
  clearInterval(refreshTimer)
  pie1?.dispose(); bar1?.dispose(); line?.dispose(); pie2?.dispose(); rose1?.dispose()
  window.removeEventListener('resize', onResize)
})
</script>

<style lang="scss" scoped>
.dashboard {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at top, #0b1224 0%, #020617 70%);
  color: #cbd5e1;
  overflow-y: auto;
  z-index: 9999;
  font-family: -apple-system, "PingFang SC", sans-serif;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(14, 165, 233, 0.06) 1px, transparent 1px),
      linear-gradient(90deg, rgba(14, 165, 233, 0.06) 1px, transparent 1px);
    background-size: 56px 56px;
    pointer-events: none;
  }
}

.topbar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  border-bottom: 1px solid rgba(14, 165, 233, 0.15);
  .left, .right {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;
    color: #94a3b8;
    font-size: 14px;
  }
  .right {
    justify-content: flex-end;
  }
  .dot {
    width: 8px;
    height: 8px;
    background: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 8px #22c55e;
    animation: pulse 1.5s infinite;
  }
  .title {
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(90deg, #22d3ee, #a78bfa, #22c55e);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    letter-spacing: 6px;
    text-align: center;
    flex: 2;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.grid {
  position: relative;
  padding: 16px 24px 24px;
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 8px;
  padding: 12px 8px;
  text-align: center;
  background: linear-gradient(180deg, rgba(14, 165, 233, 0.06), rgba(14, 165, 233, 0.01));
  .label {
    color: #94a3b8;
    font-size: 12px;
  }
  .value {
    margin-top: 6px;
    .num {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: 1px;
    }
    .unit {
      font-size: 12px;
      color: #94a3b8;
      margin-left: 4px;
    }
  }
}

.main-row {
  margin-bottom: 16px;
}

.panel {
  position: relative;
  background: rgba(14, 165, 233, 0.04);
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 16px;
  &::before {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    width: 14px;
    height: 14px;
    border-top: 2px solid #22d3ee;
    border-left: 2px solid #22d3ee;
  }
  &::after {
    content: '';
    position: absolute;
    bottom: -1px;
    right: -1px;
    width: 14px;
    height: 14px;
    border-bottom: 2px solid #22d3ee;
    border-right: 2px solid #22d3ee;
  }
}

.panel-title {
  color: #f1f5f9;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 1px;
  padding-bottom: 8px;
  margin-bottom: 6px;
  border-bottom: 1px dashed rgba(14, 165, 233, 0.2);
}

.chart {
  width: 100%;
  height: 240px;
  &.big {
    height: 280px;
  }
}

.panel.hero {
  text-align: center;
  padding: 24px 12px;
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
  }
  .hero-num {
    font-size: 88px;
    font-weight: 900;
    letter-spacing: 4px;
    line-height: 1;
    text-shadow: 0 0 30px currentColor;
  }
  .hero-label {
    margin-top: 8px;
    color: #94a3b8;
    letter-spacing: 4px;
    font-size: 16px;
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

.alert-stream {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 280px;
  overflow-y: auto;
  .alert-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 4px;
    border-left: 3px solid #0ea5e9;
    .time {
      color: #64748b;
      font-size: 12px;
      min-width: 50px;
    }
    .reason {
      flex: 1;
      color: #94a3b8;
      font-size: 12px;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }
    .score {
      font-weight: 700;
    }
  }
  .empty {
    color: #94a3b8;
    text-align: center;
    padding: 40px 0;
  }
}

.footer {
  position: relative;
  text-align: center;
  color: #64748b;
  font-size: 12px;
  padding: 12px 0 16px;
  letter-spacing: 4px;
}
</style>
