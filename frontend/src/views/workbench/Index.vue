<template>
  <div class="workbench">
    <el-card shadow="never" class="hero-card">
      <div class="hero">
        <div class="hero-text">
          <div class="title">
            欢迎回来，{{ userStore.userInfo?.real_name || '老师' }}
            <el-tag effect="dark" round size="small" type="success" class="role-tag">
              {{ userStore.userInfo?.roles?.[0]?.name || '未授权' }}
            </el-tag>
          </div>
          <div class="subtitle">
            今天是 {{ today }}，让我们一起守护每一株青苗的成长状态。
          </div>
          <div class="quick-actions">
            <el-button type="primary" :icon="VideoCamera" @click="$router.push('/classroom')">
              开始课堂分析
            </el-button>
            <el-button :icon="Histogram" @click="$router.push('/psychology')">
              心理健康档案
            </el-button>
            <el-button :icon="Bell" @click="$router.push('/alerts')">
              查看预警
            </el-button>
          </div>
        </div>
        <div class="hero-decor">
          <svg viewBox="0 0 200 160" width="200" height="160">
            <defs>
              <linearGradient id="hg" x1="0" x2="1" y1="0" y2="1">
                <stop offset="0" stop-color="#22c55e" />
                <stop offset="1" stop-color="#0ea5e9" />
              </linearGradient>
            </defs>
            <circle cx="100" cy="80" r="60" fill="url(#hg)" opacity="0.15" />
            <circle cx="100" cy="80" r="40" fill="url(#hg)" opacity="0.3" />
            <circle cx="100" cy="80" r="20" fill="url(#hg)" />
          </svg>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6" v-for="item in stats" :key="item.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-head">
            <el-icon :size="24" :color="item.color"><component :is="item.icon" /></el-icon>
            <span class="stat-label">{{ item.label }}</span>
          </div>
          <div class="stat-value">
            <span>{{ item.value }}</span>
            <span class="stat-unit">{{ item.unit }}</span>
          </div>
          <div class="stat-trend" :class="item.trendClass">
            {{ item.trend }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never">
          <template #header>
            <div class="card-head">
              <span class="card-title">本周班级综合活力指数</span>
              <el-tag size="small" effect="plain" type="info">演示数据</el-tag>
            </div>
          </template>
          <div ref="chartRef" class="chart" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="10">
        <el-card shadow="never">
          <template #header>
            <div class="card-head">
              <span class="card-title">开发路线图</span>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="item in roadmap"
              :key="item.code"
              :type="item.type"
              :hollow="item.code !== 'M1'"
              :timestamp="item.code"
            >
              <div class="roadmap-item">
                <span class="roadmap-title">{{ item.title }}</span>
                <el-tag v-if="item.code === 'M1'" size="small" type="success" effect="dark">
                  当前
                </el-tag>
                <el-tag v-else-if="item.code === 'M0'" size="small" type="success">
                  已完成
                </el-tag>
              </div>
              <div class="roadmap-desc">{{ item.desc }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { Avatar, Bell, DataLine, Histogram, School, VideoCamera } from '@element-plus/icons-vue'

import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

const today = computed(() => {
  const d = new Date()
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日 ${
    ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
  }`
})

const stats = [
  {
    label: '在校学生',
    value: 180,
    unit: '人',
    icon: Avatar,
    color: '#0ea5e9',
    trend: '本周 +0',
    trendClass: 'neutral',
  },
  {
    label: '今日预警',
    value: 0,
    unit: '条',
    icon: Bell,
    color: '#ef4444',
    trend: '需 M5 启用',
    trendClass: 'neutral',
  },
  {
    label: '本周分析视频',
    value: 0,
    unit: '段',
    icon: VideoCamera,
    color: '#22c55e',
    trend: '需 M3 启用',
    trendClass: 'neutral',
  },
  {
    label: '心理健康指数',
    value: 88,
    unit: '分',
    icon: Histogram,
    color: '#a855f7',
    trend: '↑ 1.2',
    trendClass: 'up',
  },
]

const roadmap = [
  { code: 'M0', title: '基础设施', desc: '骨架 + Docker', type: 'success' as const },
  { code: 'M1', title: '用户与权限', desc: '5 级 RBAC + 组织架构', type: 'primary' as const },
  { code: 'M2', title: 'AI 推理服务', desc: '人脸/行为/表情', type: 'info' as const },
  { code: 'M3', title: '课堂视频分析', desc: '上传 + 实时', type: 'info' as const },
  { code: 'M4', title: '心理健康', desc: '量表 + AI 对话', type: 'info' as const },
  { code: 'M5', title: '关联与预警', desc: '多维分析', type: 'info' as const },
  { code: 'M6', title: '数据大屏', desc: 'DataV 风格', type: 'info' as const },
  { code: 'M7', title: '报告中心', desc: 'AI 报告 + PDF', type: 'info' as const },
  { code: 'M8', title: '演示打磨', desc: '演示数据 + 报告', type: 'info' as const },
]

function renderChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['七1班', '七2班', '八1班'], bottom: 0 },
    grid: { left: 36, right: 16, top: 24, bottom: 36 },
    xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五'] },
    yAxis: { type: 'value', min: 60, max: 100, name: '指数' },
    series: [
      { name: '七1班', type: 'line', smooth: true, data: [82, 86, 84, 88, 90], areaStyle: { opacity: 0.1 } },
      { name: '七2班', type: 'line', smooth: true, data: [78, 80, 79, 84, 85], areaStyle: { opacity: 0.1 } },
      { name: '八1班', type: 'line', smooth: true, data: [85, 83, 88, 86, 89], areaStyle: { opacity: 0.1 } },
    ],
    color: ['#22c55e', '#0ea5e9', '#a855f7'],
  })
}

const onResize = () => chart?.resize()

onMounted(() => {
  renderChart()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})
</script>

<style lang="scss" scoped>
.workbench {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-card {
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, #f0fdf4 0%, #f0f9ff 100%);
  border: none;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 4px;
  .title {
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
    .role-tag {
      margin-left: 8px;
      vertical-align: middle;
    }
  }
  .subtitle {
    color: #64748b;
    margin: 8px 0 16px;
  }
}

.stat-row {
  margin-top: 0;
}

.stat-card {
  border-radius: 10px;
  .stat-head {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #475569;
    font-size: 13px;
  }
  .stat-value {
    margin-top: 8px;
    font-size: 28px;
    font-weight: 700;
    color: #0f172a;
    .stat-unit {
      font-size: 13px;
      color: #94a3b8;
      margin-left: 4px;
    }
  }
  .stat-trend {
    margin-top: 6px;
    font-size: 12px;
    color: #94a3b8;
    &.up {
      color: #22c55e;
    }
    &.down {
      color: #ef4444;
    }
  }
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  .card-title {
    font-weight: 600;
  }
}

.chart {
  width: 100%;
  height: 320px;
}

.roadmap-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #0f172a;
}
.roadmap-desc {
  color: #94a3b8;
  font-size: 12px;
  margin-top: 2px;
}
</style>
