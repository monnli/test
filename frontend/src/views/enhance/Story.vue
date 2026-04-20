<template>
  <div class="story-page">
    <div class="hero">
      <h1>「小李」的成长故事</h1>
      <p>这是一个虚构学生案例，演示「青苗守护者」如何在 90 天内陪伴一名学生从困境走向阳光。</p>
    </div>

    <div class="timeline">
      <div
        v-for="(s, idx) in story"
        :key="idx"
        class="step"
        :class="{ active: idx <= currentStep }"
      >
        <div class="dot" :style="{ background: s.color }">{{ idx + 1 }}</div>
        <div class="content">
          <div class="day">第 {{ s.day }} 天 · {{ s.title }}</div>
          <div class="text">{{ s.text }}</div>
          <div class="event">
            <el-tag :type="s.tagType as any" effect="dark" size="small">{{ s.tagLabel }}</el-tag>
            <span class="meta">{{ s.meta }}</span>
          </div>
        </div>
      </div>
    </div>

    <el-card shadow="never" class="metrics-card">
      <template #header><span class="card-title">小李的心理健康指数 · 90 天轨迹</span></template>
      <div ref="lineRef" class="chart" />
    </el-card>

    <div class="footer-quote">
      <div class="quote">「我们没有"治愈"小李，我们只是让他被「看见」。」</div>
      <div class="cite">—— 青苗守护者 · 心理学顾问</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'

const lineRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
const currentStep = ref(-1)
let stepTimer: any

const story = [
  {
    day: 1, title: '入学注册', text: '小李在「青苗守护者」系统中完成基础信息录入和首次心理量表测评。',
    color: '#0ea5e9', tagType: 'info', tagLabel: '入学', meta: '心理指数 85',
  },
  {
    day: 14, title: '期中考试压力', text: '系统检测到小李近期作文中出现「累」「压力大」等关键词，AI 文本分析判定为低度风险。',
    color: '#f59e0b', tagType: 'warning', tagLabel: '低度风险', meta: '心理指数 72',
  },
  {
    day: 30, title: '课堂行为异常', text: '课堂视频分析显示小李连续 3 天出现「趴桌」「玩手机」行为，预警等级升至「关注」。',
    color: '#f97316', tagType: 'warning', tagLabel: '黄色预警', meta: '心理指数 65',
  },
  {
    day: 38, title: '主动求助 AI', text: '小李在 AI 心理对话中倾诉「没有朋友，孤独」。AI 给予共情回应，并将对话标记为中度风险通知班主任。',
    color: '#ef4444', tagType: 'danger', tagLabel: '中度风险', meta: '心理指数 58',
  },
  {
    day: 40, title: '心理老师介入', text: '心理老师签收预警工单，与小李进行 1 对 1 谈话，了解其家庭关系与社交困扰。',
    color: '#0ea5e9', tagType: 'primary', tagLabel: '人工干预', meta: '工单 #142 已处理',
  },
  {
    day: 50, title: '团体心理活动', text: '心理老师组织小李所在班级开展团建活动，帮助小李建立同伴关系。',
    color: '#22c55e', tagType: 'success', tagLabel: '干预措施', meta: '心理指数 70',
  },
  {
    day: 70, title: '家校沟通', text: '班主任通过家长端与小李父母沟通，建议家庭多陪伴。家长反馈正面。',
    color: '#22c55e', tagType: 'success', tagLabel: '家校共治', meta: '心理指数 78',
  },
  {
    day: 90, title: '回归阳光', text: '小李心理指数回升至 87，量表测评从「轻度抑郁」转为「正常」。预警工单关闭。',
    color: '#22c55e', tagType: 'success', tagLabel: '已闭环', meta: '心理指数 87',
  },
]

const days = [1, 14, 30, 38, 40, 50, 70, 90]
const scores = [85, 72, 65, 58, 60, 70, 78, 87]

function render() {
  if (!lineRef.value) return
  chart?.dispose()
  chart = echarts.init(lineRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 30, bottom: 40 },
    xAxis: { type: 'category', data: days.map((d) => `第 ${d} 天`) },
    yAxis: { type: 'value', min: 0, max: 100, name: '心理指数' },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 12,
      data: scores,
      lineStyle: { color: '#0ea5e9', width: 4 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(14,165,233,0.4)' },
          { offset: 1, color: 'rgba(14,165,233,0.02)' },
        ]),
      },
      markLine: {
        silent: true,
        data: [{ yAxis: 65, lineStyle: { color: '#f59e0b', type: 'dashed' }, label: { formatter: '关注线' } }],
      },
      markPoint: {
        data: [
          { name: '低谷', xAxis: '第 38 天', yAxis: 58, value: '低谷', itemStyle: { color: '#ef4444' } },
          { name: '介入', xAxis: '第 40 天', yAxis: 60, value: '介入', itemStyle: { color: '#0ea5e9' } },
        ],
      },
    }],
  })
}

const onResize = () => chart?.resize()

function startAutoplay() {
  currentStep.value = -1
  if (stepTimer) clearInterval(stepTimer)
  stepTimer = setInterval(() => {
    currentStep.value++
    if (currentStep.value >= story.length - 1) {
      clearInterval(stepTimer)
    }
  }, 1500)
}

onMounted(() => {
  render()
  startAutoplay()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  chart?.dispose()
  if (stepTimer) clearInterval(stepTimer)
  window.removeEventListener('resize', onResize)
})
</script>

<style lang="scss" scoped>
.story-page {
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 24px;
}
.hero {
  text-align: center;
  padding: 32px 0 24px;
  h1 {
    font-size: 32px;
    margin: 0;
    background: linear-gradient(90deg, #22c55e, #0ea5e9);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }
  p {
    color: #64748b;
    margin-top: 8px;
  }
}
.timeline {
  position: relative;
  padding-left: 36px;
  &::before {
    content: '';
    position: absolute;
    left: 16px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: linear-gradient(180deg, #e5e7eb, #22c55e);
  }
}
.step {
  position: relative;
  padding: 14px 0 14px 32px;
  opacity: 0.35;
  transition: opacity 0.5s;
  &.active {
    opacity: 1;
  }
  .dot {
    position: absolute;
    left: -28px;
    top: 18px;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    color: #fff;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 0 4px #fff;
    font-size: 13px;
  }
  .content {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px 14px;
    .day {
      font-weight: 600;
      color: #0f172a;
      margin-bottom: 6px;
    }
    .text {
      color: #475569;
      line-height: 1.6;
      font-size: 13px;
    }
    .event {
      margin-top: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
      .meta {
        color: #94a3b8;
        font-size: 12px;
      }
    }
  }
}
.metrics-card {
  margin-top: 24px;
}
.card-title {
  font-weight: 600;
}
.chart {
  width: 100%;
  height: 320px;
}
.footer-quote {
  margin-top: 32px;
  text-align: center;
  padding: 24px;
  background: linear-gradient(135deg, #ecfdf5, #f0f9ff);
  border-radius: 12px;
  .quote {
    font-size: 22px;
    color: #0f172a;
    font-weight: 600;
  }
  .cite {
    margin-top: 8px;
    color: #94a3b8;
    font-size: 13px;
  }
}
</style>
