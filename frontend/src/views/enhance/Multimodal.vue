<template>
  <div class="mm-page" v-loading="loading">
    <el-card shadow="never">
      <template #header>
        <div class="head">
          <span class="card-title">多模态融合时序分析</span>
          <el-select
            v-model="studentId"
            filterable
            remote
            :remote-method="searchStudent"
            :loading="searching"
            placeholder="搜索学生"
            style="width: 240px"
            @change="load"
          >
            <el-option
              v-for="s in studentOpts"
              :key="s.id"
              :label="`${s.name}（${s.student_no}）`"
              :value="s.id"
            />
          </el-select>
        </div>
      </template>

      <div v-if="data" class="content">
        <p class="summary">{{ data.summary }}</p>
        <div ref="chartRef" class="chart" />
        <div v-if="data.anomalies?.length" class="anomalies">
          <h4>检测到 {{ data.anomalies.length }} 个跨维度异常点</h4>
          <el-tag
            v-for="a in data.anomalies"
            :key="a.date"
            type="danger"
            effect="plain"
            class="anomaly"
          >
            {{ a.date }} · {{ a.reason }}
          </el-tag>
        </div>
      </div>
      <el-empty v-else description="请选择学生" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'

import { getMultimodal, type MultimodalData } from '@/api/enhance'
import { listStudents, type Student } from '@/api/orgs'

const studentId = ref<number>()
const studentOpts = ref<Student[]>([])
const searching = ref(false)
const loading = ref(false)
const data = ref<MultimodalData | null>(null)
const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

async function searchStudent(q: string) {
  if (!q) return
  searching.value = true
  try {
    studentOpts.value = (await listStudents({ keyword: q, page: 1, page_size: 30 })).items
  } finally {
    searching.value = false
  }
}

async function load() {
  if (!studentId.value) return
  loading.value = true
  try {
    data.value = await getMultimodal(studentId.value)
    render()
  } finally {
    loading.value = false
  }
}

function render() {
  if (!chartRef.value || !data.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  const dates = data.value.series.psychology.map((p) => p.date)
  const psy = data.value.series.psychology.map((p) => p.value)
  const score = data.value.series.academic.map((p) => p.value)
  const beh = data.value.series.behavior.map((p) => p.value)

  const anomalyMarks = data.value.anomalies.map((a) => ({
    name: a.reason,
    xAxis: a.date,
    label: { formatter: '⚠' },
    itemStyle: { color: '#ef4444' },
  }))

  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['心理健康指数', '学业平均', '课堂异常次数'], bottom: 0 },
    grid: { left: 50, right: 60, top: 30, bottom: 50 },
    xAxis: { type: 'category', data: dates },
    yAxis: [
      { type: 'value', name: '心理 / 学业', min: 0, max: 100, position: 'left' },
      { type: 'value', name: '行为次数', min: 0, position: 'right' },
    ],
    series: [
      {
        name: '心理健康指数',
        type: 'line',
        smooth: true,
        data: psy,
        lineStyle: { color: '#0ea5e9', width: 3 },
        markPoint: { data: anomalyMarks },
      },
      {
        name: '学业平均',
        type: 'line',
        smooth: true,
        data: score,
        lineStyle: { color: '#22c55e', width: 2 },
      },
      {
        name: '课堂异常次数',
        type: 'bar',
        yAxisIndex: 1,
        data: beh,
        itemStyle: { color: '#f59e0b', opacity: 0.6 },
      },
    ],
  })
}

const onResize = () => chart?.resize()

onMounted(() => {
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  chart?.dispose()
  window.removeEventListener('resize', onResize)
})
</script>

<style lang="scss" scoped>
.mm-page {
  padding-bottom: 16px;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .card-title {
    font-weight: 600;
  }
}
.summary {
  color: #475569;
  margin: 0 0 12px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
}
.chart {
  width: 100%;
  height: 420px;
}
.anomalies {
  margin-top: 16px;
  h4 {
    color: #ef4444;
    margin: 0 0 8px;
  }
  .anomaly {
    margin: 0 6px 6px 0;
  }
}
</style>
