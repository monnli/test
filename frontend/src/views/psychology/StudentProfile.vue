<template>
  <div class="profile-page" v-loading="loading">
    <el-card shadow="never" class="header-card">
      <div class="hero">
        <div>
          <h2>{{ profile?.student.name }} 的心理健康档案</h2>
          <div class="subtitle">学生 ID #{{ profile?.student.id }}</div>
        </div>
        <div class="hero-stats">
          <div class="hero-stat">
            <div class="label">综合心理指数</div>
            <div class="value" :style="{ color: scoreColor(profile?.latest_score ?? 80) }">
              {{ (profile?.latest_score ?? 80).toFixed(0) }}
            </div>
          </div>
          <div class="hero-stat">
            <div class="label">当前风险</div>
            <el-tag :type="riskTag(profile?.top_risk || 'none')" effect="dark" size="large">
              {{ riskLabel(profile?.top_risk || 'none') }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never">
          <template #header>
            <div class="head">
              <span class="card-title">情绪健康指数趋势 + 7 天 AI 预测</span>
              <el-tag v-if="forecast?.risk_alert" type="danger" effect="dark" size="small">
                ⚠ 预测有风险
              </el-tag>
            </div>
          </template>
          <div ref="trendRef" class="chart" />
          <div v-if="forecast" class="forecast-tip" :class="forecast.trend_color">
            <strong>{{ forecast.trend_label }}</strong>
            <span class="meta">
              · 算法：{{ forecast.method }}
            </span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="10">
        <el-card shadow="never">
          <template #header><span class="card-title">最近测评</span></template>
          <div v-if="!profile?.assessments.length" class="empty">暂无</div>
          <el-table v-else :data="profile?.assessments" size="small" stripe>
            <el-table-column prop="scale_code" label="量表" width="100" />
            <el-table-column prop="total_score" label="得分" width="80" />
            <el-table-column label="评级">
              <template #default="{ row }">
                <el-tag :type="levelTagType(row.level_color)" effect="dark" size="small">
                  {{ row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="completed_at" label="时间" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never">
          <template #header>
            <div class="head">
              <span class="card-title">文本情绪分析</span>
              <el-button type="primary" size="small" @click="openTextDialog">新增文本分析</el-button>
            </div>
          </template>
          <div v-if="!profile?.text_analyses.length" class="empty">暂无</div>
          <div v-else>
            <div v-for="t in profile?.text_analyses" :key="t.id" class="text-row">
              <div class="row-head">
                <strong>{{ t.title || '（无标题）' }}</strong>
                <el-tag :type="riskTag(t.risk_level)" size="small" effect="dark">
                  {{ riskLabel(t.risk_level) }}
                </el-tag>
                <el-tag size="small" effect="plain">{{ t.polarity }}</el-tag>
                <span class="time">{{ t.created_at }}</span>
              </div>
              <div class="content">{{ t.content }}</div>
              <div v-if="t.summary" class="summary">归纳：{{ t.summary }}</div>
              <div v-if="t.suggestion" class="suggestion">建议：{{ t.suggestion }}</div>
              <div v-if="t.risk_keywords?.length" class="kws">
                风险词：
                <el-tag v-for="k in t.risk_keywords" :key="k" type="danger" size="small" effect="plain">
                  {{ k }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card shadow="never">
          <template #header>
            <div class="head">
              <span class="card-title">AI 心理对话</span>
              <el-button type="primary" size="small" @click="openChat">开启新对话</el-button>
            </div>
          </template>
          <div v-if="!profile?.conversations.length" class="empty">暂无</div>
          <div v-for="c in profile?.conversations" :key="c.id" class="conv-row">
            <span class="grow">{{ c.title }}</span>
            <el-tag :type="riskTag(c.risk_level)" size="small" effect="dark">
              {{ riskLabel(c.risk_level) }}
            </el-tag>
            <span class="muted">{{ c.message_count }} 条</span>
            <el-button text size="small" @click="enterConv(c.id)">查看</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 文本分析对话框 -->
    <el-dialog v-model="textDialogVisible" title="新增文本情绪分析" width="640px">
      <el-form label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="textForm.title" placeholder="如：本周周记" />
        </el-form-item>
        <el-form-item label="文本内容">
          <el-input
            v-model="textForm.content"
            type="textarea"
            :rows="6"
            placeholder="粘贴学生文本..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="textDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="textSubmitting" @click="onAnalyzeText">开始分析</el-button>
      </template>
    </el-dialog>

    <!-- 危机热线弹窗 -->
    <CrisisHotline ref="crisisRef" />

    <!-- AI 对话对话框 -->
    <el-dialog v-model="chatDialogVisible" :title="`AI 心理对话 · ${currentConv?.title || ''}`" width="640px">
      <div class="chat-history" ref="historyRef">
        <div v-for="m in messages" :key="m.id" class="chat-msg" :class="m.role">
          <div class="chat-bubble">{{ m.content }}</div>
        </div>
      </div>
      <div class="chat-input">
        <el-input v-model="chatInput" placeholder="输入消息..." @keyup.enter="onSend" />
        <el-button type="primary" :loading="chatSending" @click="onSend">发送</el-button>
      </div>
      <el-alert :closable="false" type="info" class="hint">
        AI 仅作为辅助，遇到自伤/自杀想法将自动标记并通知心理老师。
      </el-alert>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

import {
  analyzeText,
  getConversation,
  getProfile,
  postMessage,
  startConversation,
  type ConversationItem,
  type MessageItem,
  type PsychologyProfile,
} from '@/api/psychology'
import { getForecast, type ForecastResult } from '@/api/enhance'
import CrisisHotline from '@/components/CrisisHotline.vue'

const route = useRoute()
const studentId = computed(() => Number(route.params.studentId))
const loading = ref(false)
const profile = ref<PsychologyProfile | null>(null)
const trendRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

const textDialogVisible = ref(false)
const textSubmitting = ref(false)
const textForm = reactive({ title: '', content: '' })

const chatDialogVisible = ref(false)
const chatSending = ref(false)
const currentConv = ref<ConversationItem | null>(null)
const messages = ref<MessageItem[]>([])
const chatInput = ref('')
const historyRef = ref<HTMLDivElement>()
const crisisRef = ref<any>()
const forecast = ref<ForecastResult | null>(null)

function riskTag(r: string): any {
  return { none: 'success', low: 'info', medium: 'warning', high: 'danger' }[r] || 'info'
}
function riskLabel(r: string) {
  return { none: '正常', low: '轻度关注', medium: '中度关注', high: '紧急' }[r] || r
}
function levelTagType(c: string): any {
  return (
    { green: 'success', blue: 'info', orange: 'warning', red: 'danger', purple: 'danger' }[c] || 'info'
  )
}
function scoreColor(s: number): string {
  if (s >= 80) return '#22c55e'
  if (s >= 65) return '#0ea5e9'
  if (s >= 50) return '#f59e0b'
  return '#ef4444'
}

async function load() {
  loading.value = true
  try {
    profile.value = await getProfile(studentId.value)
    try {
      forecast.value = await getForecast(studentId.value, 7)
    } catch {
      forecast.value = null
    }
    renderTrend()
  } finally {
    loading.value = false
  }
}

function renderTrend() {
  if (!trendRef.value || !profile.value) return
  chart?.dispose()
  chart = echarts.init(trendRef.value)
  const tl = profile.value.timeline
  const histDates = tl.map((p) => p.date)
  const histScores = tl.map((p) => p.score)
  const fcDates = forecast.value?.forecast.map((p) => p.date) || []
  const fcScores = forecast.value?.forecast.map((p) => p.score) || []
  const allDates = [...histDates, ...fcDates]
  const histAlign = [...histScores, ...new Array(fcScores.length).fill(null)]
  const fcAlign = [...new Array(histScores.length).fill(null), ...fcScores]
  // 让历史曲线最后一点和预测连上
  if (histScores.length && fcScores.length) {
    fcAlign[histScores.length - 1] = histScores[histScores.length - 1]
  }

  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['历史', 'AI 预测（未来 7 天）'], bottom: 0 },
    grid: { left: 40, right: 16, top: 30, bottom: 32 },
    xAxis: { type: 'category', data: allDates },
    yAxis: { type: 'value', min: 0, max: 100, name: '指数' },
    series: [
      {
        name: '历史',
        type: 'line',
        smooth: true,
        data: histAlign,
        areaStyle: { opacity: 0.15 },
        lineStyle: { color: '#0ea5e9', width: 2 },
        itemStyle: { color: '#0ea5e9' },
        markLine: {
          silent: true,
          data: [
            { yAxis: 50, lineStyle: { color: '#ef4444', type: 'dashed' }, label: { formatter: '危险线' } },
            { yAxis: 70, lineStyle: { color: '#f59e0b', type: 'dashed' }, label: { formatter: '关注线' } },
          ],
        },
      },
      {
        name: 'AI 预测（未来 7 天）',
        type: 'line',
        smooth: true,
        data: fcAlign,
        lineStyle: { color: '#a855f7', width: 3, type: 'dashed' },
        itemStyle: { color: '#a855f7' },
        symbolSize: 8,
      },
    ],
  })
}

function openTextDialog() {
  textForm.title = ''
  textForm.content = ''
  textDialogVisible.value = true
}

async function onAnalyzeText() {
  textSubmitting.value = true
  try {
    await analyzeText({ student_id: studentId.value, ...textForm })
    ElMessage.success('已分析')
    textDialogVisible.value = false
    await load()
  } finally {
    textSubmitting.value = false
  }
}

async function openChat() {
  currentConv.value = await startConversation(studentId.value)
  messages.value = []
  chatDialogVisible.value = true
  await load()
}

async function enterConv(id: number) {
  const detail = await getConversation(id)
  currentConv.value = { ...detail }
  messages.value = detail.messages
  chatDialogVisible.value = true
  await nextTick()
  historyRef.value?.scrollTo({ top: 1e6 })
}

async function onSend() {
  const text = chatInput.value.trim()
  if (!text || !currentConv.value) return
  chatInput.value = ''
  chatSending.value = true
  try {
    const r = await postMessage(currentConv.value.id, text)
    messages.value.push(r.user_message, r.assistant_message)
    if (r.assistant_message.risk_level === 'high') {
      crisisRef.value?.show()
      await load()
    }
    await nextTick()
    historyRef.value?.scrollTo({ top: 1e6 })
  } finally {
    chatSending.value = false
  }
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

watch(studentId, () => load())
</script>

<style lang="scss" scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.header-card {
  border-radius: 12px;
  background: linear-gradient(135deg, #f0fdf4 0%, #f0f9ff 100%);
}
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  h2 {
    margin: 0;
    color: #0f172a;
  }
  .subtitle {
    color: #94a3b8;
    margin-top: 4px;
  }
}
.hero-stats {
  display: flex;
  gap: 32px;
}
.hero-stat {
  text-align: center;
  .label {
    color: #64748b;
    font-size: 12px;
  }
  .value {
    margin-top: 4px;
    font-size: 38px;
    font-weight: 800;
  }
}
.card-title {
  font-weight: 600;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chart {
  width: 100%;
  height: 300px;
}
.forecast-tip {
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  &.green { background: #f0fdf4; color: #166534; }
  &.blue { background: #f0f9ff; color: #075985; }
  &.orange { background: #fffbeb; color: #92400e; }
  &.red { background: #fef2f2; color: #991b1b; }
  .meta { margin-left: 8px; color: #94a3b8; font-size: 12px; }
}
.empty {
  color: #94a3b8;
  text-align: center;
  padding: 16px 0;
}
.text-row {
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
  .row-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
    .time {
      margin-left: auto;
      color: #94a3b8;
      font-size: 12px;
    }
  }
  .content {
    color: #334155;
    line-height: 1.5;
    margin: 4px 0;
  }
  .summary {
    color: #0ea5e9;
    font-size: 13px;
  }
  .suggestion {
    color: #22c55e;
    font-size: 13px;
  }
  .kws {
    margin-top: 4px;
    .el-tag {
      margin-right: 4px;
    }
  }
}
.conv-row {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
  .grow {
    flex: 1;
  }
  .muted {
    color: #94a3b8;
    font-size: 12px;
  }
}
.chat-history {
  height: 360px;
  overflow-y: auto;
  background: #f8fafc;
  border-radius: 6px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.chat-msg {
  display: flex;
  &.user {
    justify-content: flex-end;
  }
}
.chat-bubble {
  max-width: 70%;
  padding: 8px 12px;
  border-radius: 12px;
  background: #e0f2fe;
  white-space: pre-wrap;
}
.chat-msg.user .chat-bubble {
  background: #22c55e;
  color: #fff;
}
.chat-input {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.hint {
  margin-top: 12px;
}
</style>
