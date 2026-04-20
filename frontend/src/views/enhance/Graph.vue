<template>
  <div class="graph-page" v-loading="loading">
    <el-card shadow="never">
      <template #header>
        <div class="head">
          <div>
            <span class="card-title">学校知识图谱</span>
            <span class="muted">学校 → 年级 → 班级 → 学生 ↔ 教师 关系全景</span>
          </div>
          <el-button :icon="Refresh" @click="load">刷新</el-button>
        </div>
      </template>
      <div ref="graphRef" class="graph" />
      <div class="legend">
        <span>提示：拖动节点可整理布局，滚轮缩放，点击节点高亮关联</span>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'

import { getGraph, type GraphData } from '@/api/enhance'

const data = ref<GraphData | null>(null)
const loading = ref(false)
const graphRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

async function load() {
  loading.value = true
  try {
    data.value = await getGraph()
    render()
  } finally {
    loading.value = false
  }
}

function render() {
  if (!graphRef.value || !data.value) return
  chart?.dispose()
  chart = echarts.init(graphRef.value)
  chart.setOption({
    tooltip: { formatter: (p: any) => `${p.data.name}` },
    legend: [
      {
        data: data.value.categories.map((c) => c.name),
        bottom: 0,
      },
    ],
    series: [{
      type: 'graph',
      layout: 'force',
      categories: data.value.categories,
      data: data.value.nodes,
      links: data.value.links,
      roam: true,
      draggable: true,
      label: { show: true, color: '#1f2937', fontSize: 11 },
      lineStyle: { color: 'source', curveness: 0.1, opacity: 0.4 },
      emphasis: { focus: 'adjacency', label: { fontSize: 13 } },
      force: { repulsion: 80, edgeLength: [40, 80], gravity: 0.05 },
    }],
  })
}

const onResize = () => chart?.resize()

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  chart?.dispose()
  window.removeEventListener('resize', onResize)
})
</script>

<style lang="scss" scoped>
.graph-page {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .card-title {
    font-weight: 600;
    margin-right: 8px;
  }
  .muted {
    color: #94a3b8;
    font-size: 12px;
  }
}
.graph {
  width: 100%;
  height: calc(100vh - 200px);
  min-height: 500px;
}
.legend {
  margin-top: 8px;
  text-align: center;
  color: #94a3b8;
  font-size: 12px;
}
</style>
