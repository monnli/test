<template>
  <div class="workbench">
    <!-- Hero -->
    <div class="hero-card">
      <div class="hero-bg-dots" />
      <div class="hero-bg-circles">
        <div class="c c1" />
        <div class="c c2" />
        <div class="c c3" />
      </div>
      <div class="hero">
        <div class="hero-text">
          <div class="greeting">
            {{ greeting }}，<span class="name">{{ userStore.userInfo?.real_name || '老师' }}</span>
            <el-tag effect="dark" round size="small" type="success" class="role-tag">
              {{ userStore.userInfo?.roles?.[0]?.name || '未授权' }}
            </el-tag>
          </div>
          <div class="subtitle">今天是 {{ today }}，让我们一起守护每一株青苗的成长</div>
          <div class="quote">“教育是静待花开，而 AI 让我们不错过每一次绽放。”</div>
          <div class="quick-actions">
            <el-button type="primary" :icon="Monitor" size="large" @click="$router.push('/dashboard')">
              数据大屏
            </el-button>
            <el-button :icon="VideoCamera" size="large" @click="$router.push('/classroom/cameras')">
              摄像头墙
            </el-button>
            <el-button :icon="Histogram" size="large" @click="$router.push('/psychology')">
              心理档案
            </el-button>
            <el-button :icon="Bell" size="large" @click="$router.push('/alerts')">
              预警中心
            </el-button>
          </div>
        </div>
        <div class="hero-decor">
          <svg viewBox="0 0 200 200" width="220" height="220">
            <defs>
              <linearGradient id="hg" x1="0" x2="1" y1="0" y2="1">
                <stop offset="0" stop-color="#22c55e" />
                <stop offset="1" stop-color="#0ea5e9" />
              </linearGradient>
              <radialGradient id="rg" cx="50%" cy="50%" r="50%">
                <stop offset="0" stop-color="#22c55e" stop-opacity="0.4" />
                <stop offset="1" stop-color="#22c55e" stop-opacity="0" />
              </radialGradient>
            </defs>
            <circle cx="100" cy="100" r="90" fill="url(#rg)" />
            <circle cx="100" cy="100" r="60" fill="none" stroke="url(#hg)" stroke-width="2" opacity="0.5" />
            <circle cx="100" cy="100" r="40" fill="none" stroke="url(#hg)" stroke-width="2" opacity="0.7" />
            <circle cx="100" cy="100" r="22" fill="url(#hg)" />
            <path d="M100 80 a10 10 0 0 1 0 -2 c5 -2 8 0 10 5 c-2 -2 -6 -3 -10 -3z" fill="#fff" opacity="0.8" />
          </svg>
        </div>
      </div>
    </div>

    <!-- 指标卡 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6" v-for="item in stats" :key="item.label">
        <div class="stat-card" :style="{ background: item.gradient }">
          <el-icon :size="36" class="stat-icon"><component :is="item.icon" /></el-icon>
          <div class="stat-main">
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-value">
              <span class="num">{{ item.value }}</span>
              <span class="unit">{{ item.unit }}</span>
            </div>
            <div class="stat-trend">{{ item.trend }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="16">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-head">
              <div>
                <span class="card-title">本周班级综合活力指数</span>
                <span class="muted">· 基于课堂 + 心理多维数据</span>
              </div>
              <el-tag size="small" effect="plain" type="success">演示数据</el-tag>
            </div>
          </template>
          <div ref="lineChartRef" class="chart" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-head">
              <span class="card-title">今日情绪画像</span>
              <el-tag size="small" effect="plain" type="primary">实时</el-tag>
            </div>
          </template>
          <div ref="radarChartRef" class="chart" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速入口宫格 -->
    <el-card shadow="never" class="entry-card">
      <template #header>
        <div class="card-head">
          <span class="card-title">常用功能</span>
          <span class="muted">· 点击直达</span>
        </div>
      </template>
      <el-row :gutter="12" class="entries">
        <el-col :xs="12" :sm="8" :md="6" v-for="e in entries" :key="e.path">
          <div class="entry" :style="{ '--accent': e.color }" @click="$router.push(e.path)">
            <el-icon :size="24"><component :is="e.icon" /></el-icon>
            <div class="entry-name">{{ e.title }}</div>
            <div class="entry-desc">{{ e.desc }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import {
  Avatar,
  Bell,
  DataAnalysis,
  DataLine,
  Document,
  Histogram,
  Lock,
  Monitor,
  OfficeBuilding,
  PieChart,
  VideoCamera,
} from '@element-plus/icons-vue'

import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const lineChartRef = ref<HTMLDivElement>()
const radarChartRef = ref<HTMLDivElement>()
let lineChart: echarts.ECharts | null = null
let radarChart: echarts.ECharts | null = null

const today = computed(() => {
  const d = new Date()
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日 · ${
    ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
  }`
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 11) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const stats = [
  {
    label: '在校学生',
    value: 180,
    unit: '人',
    icon: Avatar,
    gradient: 'linear-gradient(135deg, #38bdf8, #0ea5e9)',
    trend: '3 年级 · 6 个班',
  },
  {
    label: '待处理预警',
    value: 5,
    unit: '条',
    icon: Bell,
    gradient: 'linear-gradient(135deg, #fb923c, #ef4444)',
    trend: '2 红 · 1 橙 · 2 黄',
  },
  {
    label: '本周分析视频',
    value: 24,
    unit: '段',
    icon: VideoCamera,
    gradient: 'linear-gradient(135deg, #4ade80, #22c55e)',
    trend: '覆盖 6 个班级',
  },
  {
    label: '心理健康指数',
    value: 88.2,
    unit: '分',
    icon: Histogram,
    gradient: 'linear-gradient(135deg, #c084fc, #a855f7)',
    trend: '↑ 1.2 较上周',
  },
]

const entries = [
  { title: '数据大屏', desc: '全校心理健康全景', path: '/dashboard', icon: Monitor, color: '#22d3ee' },
  { title: '摄像头墙', desc: '实时课堂监测', path: '/classroom/cameras', icon: VideoCamera, color: '#22c55e' },
  { title: '课表管理', desc: '课程与摄像头联动', path: '/classroom/schedule', icon: Document, color: '#0ea5e9' },
  { title: '心理健康', desc: '量表 / 文本 / AI 对话', path: '/psychology', icon: Histogram, color: '#a855f7' },
  { title: '预警中心', desc: '4 级风险工单', path: '/alerts', icon: Bell, color: '#ef4444' },
  { title: '关联分析', desc: '多维相关性', path: '/correlation', icon: DataAnalysis, color: '#f59e0b' },
  { title: '学生聚类', desc: 'K-Means 智能分群', path: '/enhance/cluster', icon: PieChart, color: '#10b981' },
  { title: '负责任 AI', desc: '伦理设计透明', path: '/ethics', icon: Lock, color: '#6366f1' },
]

function renderLine() {
  if (!lineChartRef.value) return
  lineChart?.dispose()
  lineChart = echarts.init(lineChartRef.value)
  lineChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['七1班', '七2班', '八1班', '八2班'], bottom: 0 },
    grid: { left: 40, right: 20, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五'], boundaryGap: false },
    yAxis: { type: 'value', min: 60, max: 100, name: '指数' },
    series: [
      {
        name: '七1班', type: 'line', smooth: true, data: [82, 86, 84, 88, 90],
        symbolSize: 8,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(34,197,94,0.35)' },
            { offset: 1, color: 'rgba(34,197,94,0)' },
          ]),
        },
      },
      {
        name: '七2班', type: 'line', smooth: true, data: [78, 80, 79, 84, 85],
        symbolSize: 8,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(14,165,233,0.35)' },
            { offset: 1, color: 'rgba(14,165,233,0)' },
          ]),
        },
      },
      {
        name: '八1班', type: 'line', smooth: true, data: [85, 83, 88, 86, 89],
        symbolSize: 8,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(168,85,247,0.35)' },
            { offset: 1, color: 'rgba(168,85,247,0)' },
          ]),
        },
      },
      {
        name: '八2班', type: 'line', smooth: true, data: [80, 82, 83, 85, 84],
        symbolSize: 8,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(249,115,22,0.3)' },
            { offset: 1, color: 'rgba(249,115,22,0)' },
          ]),
        },
      },
    ],
    color: ['#22c55e', '#0ea5e9', '#a855f7', '#f97316'],
  })
}

function renderRadar() {
  if (!radarChartRef.value) return
  radarChart?.dispose()
  radarChart = echarts.init(radarChartRef.value)
  radarChart.setOption({
    tooltip: {},
    radar: {
      indicator: [
        { name: '专注', max: 100 },
        { name: '愉悦', max: 100 },
        { name: '平静', max: 100 },
        { name: '参与', max: 100 },
        { name: '活力', max: 100 },
        { name: '秩序', max: 100 },
      ],
      splitArea: { areaStyle: { color: ['rgba(34,197,94,0.04)', 'rgba(14,165,233,0.04)'] } },
      axisName: { color: '#64748b' },
    },
    series: [{
      type: 'radar',
      data: [{
        value: [85, 78, 82, 72, 80, 88],
        name: '今日',
        itemStyle: { color: '#22c55e' },
        areaStyle: { opacity: 0.35 },
        lineStyle: { width: 2 },
      }],
    }],
  })
}

const onResize = () => {
  lineChart?.resize()
  radarChart?.resize()
}

onMounted(() => {
  renderLine()
  renderRadar()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  lineChart?.dispose()
  radarChart?.dispose()
  window.removeEventListener('resize', onResize)
})
</script>

<style lang="scss" scoped>
.workbench {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ============== Hero ============== */
.hero-card {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0f9ff 60%, #f5f3ff 100%);
  padding: 28px 32px;
  box-shadow: 0 4px 20px rgba(34, 197, 94, 0.08);
}

.hero-bg-dots {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(rgba(34, 197, 94, 0.12) 1px, transparent 1px),
    radial-gradient(rgba(14, 165, 233, 0.08) 1px, transparent 1px);
  background-size: 24px 24px, 48px 48px;
  background-position: 0 0, 12px 12px;
  pointer-events: none;
}
.hero-bg-circles {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  .c {
    position: absolute;
    border-radius: 50%;
    filter: blur(40px);
    opacity: 0.4;
  }
  .c1 { top: -60px; right: 10%; width: 180px; height: 180px; background: #22c55e; }
  .c2 { bottom: -80px; left: 15%; width: 220px; height: 220px; background: #0ea5e9; }
  .c3 { top: 20%; right: -60px; width: 160px; height: 160px; background: #a855f7; opacity: 0.25; }
}

.hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;

  .greeting {
    font-size: 26px;
    font-weight: 700;
    color: #0f172a;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    .name {
      background: linear-gradient(90deg, #22c55e, #0ea5e9);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      margin: 0 4px;
    }
    .role-tag {
      margin-left: 8px;
    }
  }
  .subtitle {
    color: #475569;
    margin-top: 8px;
    font-size: 14px;
  }
  .quote {
    color: #64748b;
    font-style: italic;
    margin-top: 10px;
    font-size: 13px;
  }
  .quick-actions {
    margin-top: 20px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
}

.hero-decor {
  flex-shrink: 0;
  opacity: 0.9;
  animation: float 4s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

/* ============== 指标卡 ============== */
.stat-row {
  margin-top: 0;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 22px;
  border-radius: 14px;
  color: #fff;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: default;
  margin-bottom: 0;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.15);
  }
  &::before {
    content: '';
    position: absolute;
    top: -30%;
    right: -20%;
    width: 180px;
    height: 180px;
    background: rgba(255, 255, 255, 0.15);
    border-radius: 50%;
  }
  .stat-icon {
    flex-shrink: 0;
    opacity: 0.9;
    z-index: 1;
  }
  .stat-main {
    flex: 1;
    z-index: 1;
  }
  .stat-label {
    font-size: 13px;
    opacity: 0.95;
  }
  .stat-value {
    margin-top: 4px;
    .num {
      font-size: 30px;
      font-weight: 800;
      letter-spacing: 1px;
    }
    .unit {
      font-size: 13px;
      margin-left: 4px;
      opacity: 0.9;
    }
  }
  .stat-trend {
    margin-top: 4px;
    font-size: 12px;
    opacity: 0.9;
  }
}

/* ============== 图表卡 ============== */
.chart-card {
  border-radius: 12px;
  border: 1px solid #f1f5f9;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .card-title {
    font-weight: 600;
    color: #0f172a;
  }
  .muted {
    color: #94a3b8;
    font-size: 12px;
    margin-left: 4px;
  }
}
.chart {
  width: 100%;
  height: 300px;
}

/* ============== 快速入口宫格 ============== */
.entry-card {
  border-radius: 12px;
  border: 1px solid #f1f5f9;
}
.entries {
  margin: 0;
}
.entry {
  --accent: #0ea5e9;
  position: relative;
  padding: 18px 16px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f8fafc, #fff);
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 12px;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: var(--accent);
    border-radius: 3px 0 0 3px;
    transform: scaleY(0.4);
    transition: transform 0.2s;
  }
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
    border-color: var(--accent);
    .entry-name {
      color: var(--accent);
    }
    &::before {
      transform: scaleY(1);
    }
  }
  :deep(.el-icon) {
    color: var(--accent);
  }
  .entry-name {
    margin-top: 8px;
    font-weight: 600;
    color: #0f172a;
    transition: color 0.2s;
  }
  .entry-desc {
    margin-top: 2px;
    color: #94a3b8;
    font-size: 12px;
  }
}
</style>
