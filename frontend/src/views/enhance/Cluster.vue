<template>
  <div class="cluster-page" v-loading="loading">
    <el-card shadow="never">
      <template #header>
        <div class="head">
          <div>
            <span class="card-title">学生群体智能聚类</span>
            <span class="muted">基于 4 维特征（心理 + 学业 + 量表 + 课堂）K-Means 自动分群</span>
          </div>
          <div class="right">
            簇数：
            <el-input-number v-model="numClusters" :min="3" :max="8" size="small" @change="load" />
            <el-button :icon="Refresh" @click="load">刷新</el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="16">
        <el-col :xs="24" :md="14">
          <h4>聚类散点图（{{ data?.total || 0 }} 名学生）</h4>
          <div ref="scatterRef" class="chart" />
        </el-col>
        <el-col :xs="24" :md="10">
          <h4>群体画像</h4>
          <div v-for="c in data?.clusters || []" :key="c.cluster_id" class="cluster-row">
            <div class="row-head">
              <span class="dot" :style="{ background: c.color }" />
              <strong>{{ c.name }}</strong>
              <el-tag effect="dark" type="info" size="small">{{ c.count }} 人</el-tag>
            </div>
            <div class="metrics">
              心理 {{ c.avg_psy }} · 学业 {{ c.avg_score }} · 量表 {{ c.avg_scale }} · 课堂异常 {{ c.avg_abnormal }}
            </div>
            <div class="advice">建议：{{ c.advice }}</div>
            <div class="samples">
              代表学生：
              <el-tag
                v-for="n in c.sample_students"
                :key="n"
                size="small"
                effect="plain"
                class="sample-tag"
                >{{ n }}</el-tag
              >
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'

import { getCluster, type ClusterResult } from '@/api/enhance'

const data = ref<ClusterResult | null>(null)
const loading = ref(false)
const numClusters = ref(5)
const scatterRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

async function load() {
  loading.value = true
  try {
    data.value = await getCluster(numClusters.value)
    render()
  } finally {
    loading.value = false
  }
}

function render() {
  if (!scatterRef.value || !data.value) return
  chart?.dispose()
  chart = echarts.init(scatterRef.value)
  const series = data.value.clusters.map((c) => ({
    name: c.name,
    type: 'scatter' as const,
    symbolSize: 12,
    itemStyle: { color: c.color, opacity: 0.85 },
    data: data.value!.points
      .filter((p) => p.cluster === c.cluster_id)
      .map((p) => ({ value: [p.x, p.y], name: p.name })),
  }))
  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => `${p.data.name}<br/>${data.value!.axis_labels.x}: ${p.data.value[0]}<br/>${data.value!.axis_labels.y}: ${p.data.value[1]}`,
    },
    legend: { bottom: 0, type: 'scroll' },
    grid: { left: 50, right: 16, top: 24, bottom: 50 },
    xAxis: { name: data.value.axis_labels.x, min: 0, max: 100 },
    yAxis: { name: data.value.axis_labels.y, min: 0, max: 100 },
    series,
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
.cluster-page {
  padding-bottom: 16px;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  .card-title {
    font-weight: 600;
    margin-right: 8px;
  }
  .muted {
    color: #94a3b8;
    font-size: 12px;
  }
  .right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}
.chart {
  width: 100%;
  height: 480px;
}
h4 {
  margin: 8px 0;
  color: #0f172a;
  font-size: 14px;
}
.cluster-row {
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 10px;
  .row-head {
    display: flex;
    align-items: center;
    gap: 8px;
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
  }
  .metrics {
    margin-top: 6px;
    color: #64748b;
    font-size: 12px;
  }
  .advice {
    margin-top: 4px;
    color: #22c55e;
    font-size: 13px;
  }
  .samples {
    margin-top: 6px;
    color: #475569;
    font-size: 12px;
  }
  .sample-tag {
    margin-right: 4px;
  }
}
</style>
