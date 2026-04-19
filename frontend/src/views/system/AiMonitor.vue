<template>
  <div class="ai-monitor">
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="24" :md="10">
        <el-card shadow="never" class="status-card">
          <template #header>
            <div class="card-head">
              <span class="title">AI 服务健康状态</span>
              <el-button text :icon="Refresh" :loading="loading" @click="refreshAll">
                刷新
              </el-button>
            </div>
          </template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="服务状态">
              <el-tag :type="health ? 'success' : 'danger'" effect="dark">
                {{ health?.status || '未连接' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="推理设备">{{ health?.device || '—' }}</el-descriptions-item>
            <el-descriptions-item label="时间戳">{{
              health?.timestamp ? formatTs(health.timestamp) : '—'
            }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="14">
        <el-card shadow="never" class="status-card">
          <template #header>
            <div class="card-head">
              <span class="title">流水线加载状态</span>
              <el-tag size="small" effect="plain" type="info">
                mock = 未安装真实模型权重，使用兜底逻辑
              </el-tag>
            </div>
          </template>
          <el-table :data="pipelines" stripe size="small">
            <el-table-column label="流水线" width="120">
              <template #default="{ row }">
                <strong>{{ pipelineLabel(row.name) }}</strong>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" effect="dark" size="small">
                  {{ statusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="device" label="设备" width="80" />
            <el-table-column label="错误信息">
              <template #default="{ row }">
                <span class="err">{{ row.error || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button
                  text
                  type="primary"
                  size="small"
                  :loading="loadingName === row.name"
                  @click="onLoad(row.name)"
                >
                  加载
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <span class="card-title">AI 功能在线测试</span>
      </template>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="文本情绪分析" name="sentiment">
          <el-input
            v-model="sentimentText"
            type="textarea"
            :rows="4"
            placeholder="请输入一段学生文本，如「今天考试没考好，心里特别难过」"
          />
          <div class="actions">
            <el-button type="primary" :loading="sentimentLoading" @click="onSentiment">
              分析
            </el-button>
          </div>
          <div v-if="sentimentResult" class="result-box">
            <div>
              极性：<el-tag :type="polarityTag(sentimentResult.polarity)" effect="dark">
                {{ sentimentResult.polarity }}
              </el-tag>
            </div>
            <div>
              风险等级：
              <el-tag :type="riskTag(sentimentResult.risk_level)" effect="dark">
                {{ riskLabel(sentimentResult.risk_level) }}
              </el-tag>
            </div>
            <div v-if="sentimentResult.risk_keywords?.length">
              风险词：
              <el-tag
                v-for="k in sentimentResult.risk_keywords"
                :key="k"
                type="danger"
                effect="plain"
                class="tag"
                >{{ k }}</el-tag
              >
            </div>
            <div v-if="sentimentResult.emotion_tags?.length">
              情绪标签：
              <el-tag
                v-for="t in sentimentResult.emotion_tags"
                :key="t"
                type="success"
                effect="plain"
                class="tag"
                >{{ t }}</el-tag
              >
            </div>
            <div v-if="sentimentResult.reason" class="reason">
              依据：{{ sentimentResult.reason }}
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="AI 心理对话" name="chat">
          <div class="chat-box">
            <div class="chat-history" ref="historyRef">
              <div
                v-for="(m, idx) in chatMessages"
                :key="idx"
                class="chat-msg"
                :class="m.role"
              >
                <div class="chat-bubble">{{ m.content }}</div>
              </div>
              <div v-if="chatLoading" class="chat-msg assistant">
                <div class="chat-bubble typing">…</div>
              </div>
            </div>
            <div class="chat-input">
              <el-input
                v-model="chatInput"
                placeholder="和 AI 心理辅导员聊聊…"
                @keyup.enter="onChat"
              />
              <el-button type="primary" :loading="chatLoading" @click="onChat">发送</el-button>
              <el-button @click="resetChat">清空</el-button>
            </div>
            <div class="chat-hint">
              <el-icon><WarningFilled /></el-icon>
              仅为 AI 辅助演示，不构成心理诊断。遇到自伤/自杀想法请联系老师或拨打 12320。
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="表情 / 行为识别" name="image">
          <el-upload
            ref="uploadRef"
            class="uploader"
            drag
            :show-file-list="false"
            :before-upload="beforeUpload"
            :auto-upload="false"
            accept="image/*"
            @change="onImageChange"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽或点击选择一张含人脸的图片，识别表情与课堂行为
            </div>
          </el-upload>
          <div v-if="imagePreview" class="image-area">
            <img :src="imagePreview" class="preview" />
            <div class="image-actions">
              <el-button type="primary" :loading="imageLoading" @click="onImageAnalyze">
                分析
              </el-button>
              <el-button @click="imagePreview = ''; imageResult = null">清空</el-button>
            </div>
          </div>
          <div v-if="imageResult" class="result-box">
            <h4>表情识别</h4>
            <div>
              主表情：
              <el-tag effect="dark" type="success">
                {{ imageResult.emotion?.emotion_cn }} （{{
                  (imageResult.emotion?.confidence * 100).toFixed(1)
                }}%）
              </el-tag>
            </div>
            <h4>行为检测</h4>
            <div>
              识别到：
              <el-tag
                v-for="(count, label) in imageResult.behavior?.summary || {}"
                :key="label"
                class="tag"
                effect="plain"
              >
                {{ label }} × {{ count }}
              </el-tag>
              <span v-if="!Object.keys(imageResult.behavior?.summary || {}).length">无</span>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, UploadFilled, WarningFilled } from '@element-plus/icons-vue'

import {
  aiBehavior,
  aiChat,
  aiEmotion,
  aiSentiment,
  getAiHealth,
  getAiPipelines,
  loadPipeline,
  type ChatMessage,
  type PipelineStatus,
  type SentimentResult,
} from '@/api/ai'

const loading = ref(false)
const loadingName = ref<string>('')
const health = ref<any>(null)
const pipelines = ref<PipelineStatus[]>([])
const activeTab = ref('sentiment')

// 情绪分析
const sentimentText = ref('今天考试没考好，心里特别难过，还有一点烦躁。')
const sentimentLoading = ref(false)
const sentimentResult = ref<SentimentResult | null>(null)

// 对话
const chatMessages = ref<ChatMessage[]>([])
const chatInput = ref('')
const chatLoading = ref(false)
const historyRef = ref<HTMLDivElement>()

// 图像分析
const imagePreview = ref('')
const imageLoading = ref(false)
const imageResult = ref<any>(null)

function pipelineLabel(name: string) {
  return (
    { face: '人脸识别', emotion: '表情识别', behavior: '行为检测', text: '文本分析' }[name] || name
  )
}

function statusTag(s: string): any {
  return { ready: 'success', mock: 'warning', loading: 'info', error: 'danger' }[s] || 'info'
}

function statusLabel(s: string) {
  return (
    { not_loaded: '未加载', loading: '加载中', ready: '就绪', mock: '降级', error: '错误' }[s] || s
  )
}

function polarityTag(p: string): any {
  return p === '正面' ? 'success' : p === '负面' ? 'danger' : 'info'
}

function riskTag(r: string): any {
  return { none: 'success', low: 'info', medium: 'warning', high: 'danger' }[r] || 'info'
}

function riskLabel(r: string) {
  return { none: '无风险', low: '轻度', medium: '中度', high: '高风险' }[r] || r
}

function formatTs(ts: number) {
  return new Date(ts * 1000).toLocaleString('zh-CN')
}

async function refreshAll() {
  loading.value = true
  try {
    const [h, p] = await Promise.all([getAiHealth(), getAiPipelines()])
    health.value = h
    pipelines.value = p.pipelines
  } finally {
    loading.value = false
  }
}

async function onLoad(name: string) {
  loadingName.value = name
  try {
    await loadPipeline(name)
    ElMessage.success(`${pipelineLabel(name)} 加载完成`)
    await refreshAll()
  } finally {
    loadingName.value = ''
  }
}

async function onSentiment() {
  if (!sentimentText.value.trim()) {
    ElMessage.warning('请输入文本')
    return
  }
  sentimentLoading.value = true
  try {
    sentimentResult.value = await aiSentiment(sentimentText.value)
  } finally {
    sentimentLoading.value = false
  }
}

async function onChat() {
  const text = chatInput.value.trim()
  if (!text) return
  chatMessages.value.push({ role: 'user', content: text })
  chatInput.value = ''
  await nextTick()
  historyRef.value?.scrollTo({ top: 1e6 })
  chatLoading.value = true
  try {
    const result = await aiChat(chatMessages.value)
    chatMessages.value.push({ role: 'assistant', content: result.reply })
    if (result.risk_level === 'high') {
      ElMessage.warning({
        message: '检测到高风险表达，已标记预警（预警流程将于 M5 实现）',
        duration: 4000,
      })
    }
  } finally {
    chatLoading.value = false
    await nextTick()
    historyRef.value?.scrollTo({ top: 1e6 })
  }
}

function resetChat() {
  chatMessages.value = []
}

function beforeUpload() {
  return false
}

function onImageChange(file: any) {
  const reader = new FileReader()
  reader.onload = () => {
    imagePreview.value = reader.result as string
    imageResult.value = null
  }
  reader.readAsDataURL(file.raw)
}

async function onImageAnalyze() {
  if (!imagePreview.value) return
  imageLoading.value = true
  try {
    const [emotion, behavior] = await Promise.all([
      aiEmotion(imagePreview.value),
      aiBehavior(imagePreview.value),
    ])
    imageResult.value = { emotion, behavior }
  } finally {
    imageLoading.value = false
  }
}

onMounted(refreshAll)
</script>

<style lang="scss" scoped>
.ai-monitor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-row {
  margin-top: 0;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  .title {
    font-weight: 600;
  }
}

.card-title {
  font-weight: 600;
}

.actions {
  margin-top: 12px;
}

.result-box {
  margin-top: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  > div {
    margin-bottom: 8px;
  }
  h4 {
    margin: 12px 0 8px;
    color: #0f172a;
  }
}

.tag {
  margin: 0 4px 4px 0;
}

.reason {
  color: #64748b;
  font-size: 12px;
}

.err {
  color: #ef4444;
  font-size: 12px;
  word-break: break-all;
}

.chat-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-history {
  height: 360px;
  overflow-y: auto;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-msg {
  display: flex;
  &.user {
    justify-content: flex-end;
  }
  &.assistant {
    justify-content: flex-start;
  }
}

.chat-bubble {
  max-width: 70%;
  padding: 8px 12px;
  border-radius: 12px;
  background: #e0f2fe;
  color: #0f172a;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-msg.user .chat-bubble {
  background: #22c55e;
  color: #fff;
}

.chat-bubble.typing {
  color: #94a3b8;
  letter-spacing: 4px;
}

.chat-input {
  display: flex;
  gap: 8px;
}

.chat-hint {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 4px;
}

.uploader {
  :deep(.el-upload-dragger) {
    width: 100%;
  }
}

.image-area {
  margin-top: 12px;
}

.preview {
  max-width: 100%;
  max-height: 320px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.image-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.status-card {
  height: 100%;
}
</style>
