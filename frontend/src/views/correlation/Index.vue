<template>
  <div class="corr-page">
    <el-card shadow="never">
      <template #header>
        <div class="head">
          <span class="card-title">多维关联分析</span>
          <el-button :icon="Refresh" @click="load">刷新</el-button>
        </div>
      </template>
      <p class="hint">
        基于学生的「心理健康指数 / 学业平均分 / 量表得分 / 课堂行为 / 综合风险评分」5 个维度计算两两相关性，识别需要重点关注的群体特征。
      </p>
      <el-row :gutter="16">
        <el-col :xs="24" :md="12">
          <h4>风险评分分布</h4>
          <div ref="distRef" class="chart" />
        </el-col>
        <el-col :xs="24" :md="12">
          <h4>心理指数 ↔ 学业平均分 散点</h4>
          <div ref="scatterRef" class="chart" />
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :xs="24">
          <h4>相关性热力图</h4>
          <div ref="heatRef" class="chart" style="height: 400px" />
        </el-col>
      </el-row>

      <el-divider>学生明细（按风险评分降序）</el-divider>
      <el-table :data="topRisk" stripe size="small">
        <el-table-column label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="levelTag(row.level)" effect="dark" size="small">
              {{ levelLabel(row.level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险评分" width="100">
          <template #default="{ row }">
            <strong :style="{ color: levelColor(row.level) }">{{ row.risk_score.toFixed(0) }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="psy_30d" label="心理指数 30d" width="110" />
        <el-table-column prop="score_avg" label="学业平均" width="100" />
        <el-table-column prop="scale_score" label="量表得分" width="100" />
        <el-table-column prop="phone_count" label="玩手机次数" width="110" />
        <el-table-column label="档案" width="100">
          <template #default="{ row }">
            <el-button text type="primary" @click="$router.push(`/psychology/student/${row.student_id}`)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'

import { getCorrelationMatrix, type CorrelationItem } from '@/api/alerts'

const items = ref<CorrelationItem[]>([])
const distRef = ref<HTMLDivElement>()
const scatterRef = ref<HTMLDivElement>()
const heatRef = ref<HTMLDivElement>()
let dist: echarts.ECharts | null = null
let scat: echarts.ECharts | null = null
let heat: echarts.ECharts | null = null

const topRisk = computed(() =>
  [...items.value].sort((a, b) => b.risk_score - a.risk_score).slice(0, 30),
)

function levelTag(l: string): any {
  return { red: 'danger', orange: 'warning', yellow: 'warning', green: 'success' }[l] || 'info'
}
function levelLabel(l: string) {
  return { red: '紧急', orange: '重点', yellow: '关注', green: '正常' }[l] || l
}
function levelColor(l: string) {
  return { red: '#ef4444', orange: '#f97316', yellow: '#f59e0b', green: '#22c55e' }[l] || '#94a3b8'
}

async function load() {
  const data = await getCorrelationMatrix()
  items.value = data.items
  render()
}

function render() {
  if (!items.value.length) return
  const list = items.value

  // 风险评分分布
  if (distRef.value) {
    dist?.dispose()
    dist = echarts.init(distRef.value)
    const buckets = [0, 20, 40, 60, 80, 100]
    const labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
    const counts = labels.map((_, i) => list.filter((d) => d.risk_score >= buckets[i] && d.risk_score < buckets[i + 1]).length)
    dist.setOption({
      tooltip: {},
      grid: { left: 40, right: 16, top: 24, bottom: 30 },
      xAxis: { type: 'category', data: labels },
      yAxis: { type: 'value', name: '人数' },
      series: [
        {
          type: 'bar',
          data: counts.map((c, i) => ({
            value: c,
            itemStyle: { color: ['#22c55e', '#eab308', '#f59e0b', '#f97316', '#ef4444'][i] },
          })),
        },
      ],
    })
  }

  // 散点
  if (scatterRef.value) {
    scat?.dispose()
    scat = echarts.init(scatterRef.value)
    scat.setOption({
      tooltip: {
        formatter: (p: any) => `${p.data.name}<br/>心理：${p.data.value[0]}<br/>学业：${p.data.value[1]}`,
      },
      grid: { left: 40, right: 16, top: 24, bottom: 36 },
      xAxis: { name: '心理指数', min: 0, max: 100 },
      yAxis: { name: '学业平均', min: 0, max: 100 },
      series: [
        {
          type: 'scatter',
          symbolSize: 10,
          data: list.map((d) => ({
            name: d.name,
            value: [d.psy_30d, d.score_avg],
            itemStyle: { color: levelColor(d.level), opacity: 0.8 },
          })),
        },
      ],
    })
  }

  // 热力图（相关系数）
  if (heatRef.value) {
    heat?.dispose()
    heat = echarts.init(heatRef.value)
    const fields = ['psy_30d', 'score_avg', 'scale_score', 'phone_count', 'risk_score']
    const labels = ['心理指数', '学业平均', '量表得分', '玩手机', '风险评分']
    const matrix: number[][] = []
    fields.forEach((a, i) => {
      fields.forEach((b, j) => {
        const corr = pearson(list.map((d: any) => d[a]), list.map((d: any) => d[b]))
        matrix.push([i, j, +corr.toFixed(2)])
      })
    })
    heat.setOption({
      tooltip: { position: 'top' },
      grid: { left: 100, right: 60, top: 30, bottom: 60 },
      xAxis: { type: 'category', data: labels, axisLabel: { rotate: 30 } },
      yAxis: { type: 'category', data: labels },
      visualMap: { min: -1, max: 1, calculable: true, orient: 'horizontal', bottom: 0, inRange: { color: ['#0ea5e9', '#fff', '#ef4444'] } },
      series: [
        {
          type: 'heatmap',
          data: matrix,
          label: { show: true },
        },
      ],
    })
  }
}

function pearson(x: number[], y: number[]): number {
  if (!x.length) return 0
  const mx = avg(x)
  const my = avg(y)
  let num = 0
  let dx = 0
  let dy = 0
  for (let i = 0; i < x.length; i++) {
    const ax = x[i] - mx
    const ay = y[i] - my
    num += ax * ay
    dx += ax * ax
    dy += ay * ay
  }
  const denom = Math.sqrt(dx * dy)
  return denom ? num / denom : 0
}
function avg(a: number[]) {
  return a.reduce((s, v) => s + v, 0) / a.length
}

const onResize = () => {
  dist?.resize()
  scat?.resize()
  heat?.resize()
}

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  dist?.dispose()
  scat?.dispose()
  heat?.dispose()
  window.removeEventListener('resize', onResize)
})
</script>

<style lang="scss" scoped>
.corr-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .card-title {
    font-weight: 600;
  }
}
.hint {
  color: #64748b;
  margin: 0 0 12px;
}
.chart {
  width: 100%;
  height: 280px;
}
h4 {
  margin: 8px 0;
  color: #0f172a;
  font-size: 14px;
}
</style>
