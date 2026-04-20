<template>
  <div class="interv-page" v-loading="loading">
    <el-row :gutter="16">
      <el-col :xs="12" :md="6" v-for="m in metrics" :key="m.label">
        <el-card shadow="hover" class="stat-card">
          <div class="m-label">{{ m.label }}</div>
          <div class="m-value" :style="{ color: m.color }">
            {{ m.value }}<span class="m-unit">{{ m.unit }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span class="card-title">预警处理漏斗</span></template>
          <div ref="funnelRef" class="chart" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span class="card-title">干预手段分布</span></template>
          <div ref="actionRef" class="chart" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <div class="head">
          <span class="card-title">查看具体预警的闭环效果（前 14 天 vs 后 14 天对比）</span>
          <el-input-number v-model="alertId" :min="1" size="small" placeholder="预警 ID" />
          <el-button type="primary" size="small" @click="loadJourney">查看</el-button>
        </div>
      </template>
      <div v-if="journey">
        <el-row :gutter="16">
          <el-col :xs="24" :md="14">
            <h4>心理健康指数 · 干预前后</h4>
            <div ref="cmpRef" class="chart" />
          </el-col>
          <el-col :xs="24" :md="10">
            <h4>事件时间轴</h4>
            <el-timeline>
              <el-timeline-item
                v-for="(e, i) in journey.timeline_events"
                :key="i"
                :color="e.color"
                :timestamp="e.time"
              >
                {{ e.label }}
              </el-timeline-item>
            </el-timeline>
            <div class="cmp-summary">
              <div>干预前平均：<strong>{{ journey.comparison.avg_before }}</strong></div>
              <div>干预后平均：<strong>{{ journey.comparison.avg_after }}</strong></div>
              <div>
                改善：
                <el-tag
                  :type="journey.comparison.improvement > 0 ? 'success' : 'danger'"
                  effect="dark"
                >
                  {{ journey.comparison.improvement > 0 ? '+' : '' }}{{ journey.comparison.improvement }}
                </el-tag>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

import {
  getAlertJourney,
  getInterventionOverview,
  type AlertJourney,
  type InterventionOverview,
} from '@/api/enhance'

const overview = ref<InterventionOverview | null>(null)
const journey = ref<AlertJourney | null>(null)
const loading = ref(false)
const alertId = ref<number>(1)

const funnelRef = ref<HTMLDivElement>()
const actionRef = ref<HTMLDivElement>()
const cmpRef = ref<HTMLDivElement>()
let funnel: echarts.ECharts | null = null
let action: echarts.ECharts | null = null
let cmp: echarts.ECharts | null = null

const metrics = computed(() => [
  { label: '总预警数', value: overview.value?.total_alerts ?? 0, unit: '条', color: '#0ea5e9' },
  { label: '已处理', value: overview.value?.resolved_count ?? 0, unit: '条', color: '#22c55e' },
  { label: '处理成功率', value: overview.value?.success_rate ?? 0, unit: '%', color: '#a855f7' },
  { label: '平均处理时长', value: overview.value?.avg_hours ?? 0, unit: '小时', color: '#f59e0b' },
])

async function loadOverview() {
  loading.value = true
  try {
    overview.value = await getInterventionOverview()
    renderOverview()
  } finally {
    loading.value = false
  }
}

async function loadJourney() {
  if (!alertId.value) return
  try {
    journey.value = await getAlertJourney(alertId.value)
    renderCompare()
  } catch (e) {
    journey.value = null
  }
}

function renderOverview() {
  if (funnelRef.value && overview.value) {
    funnel?.dispose()
    funnel = echarts.init(funnelRef.value)
    funnel.setOption({
      tooltip: {},
      series: [{
        type: 'funnel',
        data: overview.value.funnel,
        label: { color: '#0f172a' },
        itemStyle: { borderColor: '#fff', borderWidth: 2 },
      }],
    })
  }
  if (actionRef.value && overview.value) {
    action?.dispose()
    action = echarts.init(actionRef.value)
    action.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie',
        radius: ['35%', '70%'],
        data: overview.value.by_action.length
          ? overview.value.by_action
          : [{ name: '暂无数据', value: 1 }],
        label: { color: '#0f172a' },
      }],
      color: ['#22c55e', '#0ea5e9', '#a855f7', '#f59e0b', '#ef4444'],
    })
  }
}

function renderCompare() {
  if (!cmpRef.value || !journey.value) return
  cmp?.dispose()
  cmp = echarts.init(cmpRef.value)
  const cmpData = journey.value.comparison
  cmp.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['干预前 14 天', '干预后 14 天'], bottom: 0 },
    grid: { left: 40, right: 16, top: 24, bottom: 36 },
    xAxis: {
      type: 'category',
      data: [...cmpData.before, ...cmpData.after].map((p) => p.date),
    },
    yAxis: { type: 'value', min: 0, max: 100 },
    series: [
      {
        name: '干预前 14 天',
        type: 'line',
        smooth: true,
        data: [...cmpData.before.map((p) => p.score), ...new Array(cmpData.after.length).fill(null)],
        lineStyle: { color: '#ef4444', width: 3 },
      },
      {
        name: '干预后 14 天',
        type: 'line',
        smooth: true,
        data: [...new Array(cmpData.before.length).fill(null), ...cmpData.after.map((p) => p.score)],
        lineStyle: { color: '#22c55e', width: 3 },
      },
    ],
  })
}

const onResize = () => {
  funnel?.resize()
  action?.resize()
  cmp?.resize()
}

onMounted(() => {
  loadOverview()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  funnel?.dispose()
  action?.dispose()
  cmp?.dispose()
  window.removeEventListener('resize', onResize)
})
</script>

<style lang="scss" scoped>
.interv-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.stat-card {
  border-radius: 10px;
  text-align: center;
  margin-bottom: 16px;
  .m-label {
    color: #64748b;
    font-size: 12px;
  }
  .m-value {
    margin-top: 6px;
    font-size: 28px;
    font-weight: 700;
    .m-unit {
      font-size: 12px;
      color: #94a3b8;
      margin-left: 4px;
    }
  }
}
.card-title {
  font-weight: 600;
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.chart {
  width: 100%;
  height: 320px;
}
h4 {
  color: #0f172a;
  margin: 0 0 8px;
}
.cmp-summary {
  margin-top: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
  > div {
    margin: 4px 0;
  }
}
</style>
