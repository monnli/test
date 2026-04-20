<template>
  <div class="ethics-page" v-loading="loading">
    <el-card shadow="never" class="hero-card">
      <div class="hero">
        <div class="hero-text">
          <h2><el-icon><Lock /></el-icon> 负责任 AI 仪表盘</h2>
          <p>所有 AI 输出仅作辅助，最终判断由人类专业人员做出。本页面公开本系统的伦理设计与运行数据。</p>
        </div>
        <div class="hero-stat">
          <div class="big">{{ data?.stats.explainable_rate ?? 0 }}%</div>
          <div class="muted">AI 决策可解释率</div>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :xs="12" :md="8" v-for="p in data?.principles" :key="p.key">
        <el-card shadow="hover" class="principle-card">
          <div class="head">
            <el-icon :size="22" color="#22c55e"><component :is="iconMap[p.icon] || 'Aim'" /></el-icon>
            <span class="title">{{ p.key }}</span>
            <el-tag effect="dark" type="success" size="small">{{ p.value }}</el-tag>
          </div>
          <div class="desc">{{ p.desc }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never">
          <template #header><span class="card-title">实时伦理保护数据</span></template>
          <el-row :gutter="16">
            <el-col :span="8" v-for="m in metrics" :key="m.label">
              <div class="metric">
                <div class="m-label">{{ m.label }}</div>
                <div class="m-value" :style="{ color: m.color }">{{ m.value }}<span class="m-unit">{{ m.unit }}</span></div>
              </div>
            </el-col>
          </el-row>
          <el-divider>风险词典（系统识别敏感表达）</el-divider>
          <div class="dict">
            <div class="dict-row">
              <el-tag type="danger" effect="dark">高风险</el-tag>
              <span class="kw" v-for="k in data?.risk_dictionary.high" :key="k">{{ k }}</span>
            </div>
            <div class="dict-row">
              <el-tag type="warning" effect="dark">中风险</el-tag>
              <span class="kw med" v-for="k in data?.risk_dictionary.medium" :key="k">{{ k }}</span>
            </div>
            <div class="dict-row">
              <el-tag type="info" effect="dark">轻风险</el-tag>
              <span class="kw low" v-for="k in data?.risk_dictionary.low" :key="k">{{ k }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="10">
        <el-card shadow="never">
          <template #header><span class="card-title">AI 心理对话系统提示词（公开）</span></template>
          <pre class="prompt-block">{{ data?.system_prompt_excerpt }}</pre>
          <el-alert type="info" :closable="false" class="alert">
            <template #title>
              我们公开 AI 系统提示词，让你看到「我们是怎么设计 AI 不越界的」。
            </template>
          </el-alert>
        </el-card>

        <el-card shadow="never" class="audit-card">
          <template #header><span class="card-title">最近伦理保护动作日志</span></template>
          <div v-for="(log, idx) in data?.audit_logs" :key="idx" class="audit-row">
            <span class="time">{{ log.time }}</span>
            <el-tag size="small" effect="plain">{{ log.type }}</el-tag>
            <span class="detail">{{ log.detail }}</span>
          </div>
          <div v-if="!data?.audit_logs?.length" class="empty">暂无</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="footer-note">
      <template #header><span class="card-title">我们的承诺</span></template>
      <ul>
        <li>✅ <strong>本地化部署</strong>：所有 AI 推理可在校园内网完成，敏感数据可不出校门</li>
        <li>✅ <strong>开源核心代码</strong>：接受社会监督，代码在 GitHub 公开</li>
        <li>✅ <strong>关键阈值可配置</strong>：风险评分、预警阈值由学校心理学教师调整</li>
        <li>✅ <strong>数据生命周期</strong>：学生离校后默认软删除，可应申请彻底删除</li>
        <li>✅ <strong>避免标签化</strong>：系统不输出"抑郁学生""问题学生"等永久性标签</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Aim, Avatar, Help, Lock, User, View } from '@element-plus/icons-vue'

import { getEthicsOverview, type EthicsOverview } from '@/api/ethics'

const data = ref<EthicsOverview | null>(null)
const loading = ref(false)

const iconMap: Record<string, any> = { Aim, Avatar, Help, Lock, User, View }

const metrics = computed(() => {
  const s = data.value?.stats
  return [
    { label: '已脱敏人脸', value: s?.face_anonymized ?? 0, unit: '张', color: '#22c55e' },
    { label: '高风险拦截', value: s?.high_risk_blocked ?? 0, unit: '次', color: '#ef4444' },
    { label: '人工介入率', value: s?.human_intervention_rate ?? 0, unit: '%', color: '#0ea5e9' },
    { label: '可解释 AI', value: s?.explainable_rate ?? 0, unit: '%', color: '#a855f7' },
    { label: '在校学生', value: s?.total_students ?? 0, unit: '人', color: '#22c55e' },
    { label: '总预警数', value: s?.total_alerts ?? 0, unit: '条', color: '#f59e0b' },
  ]
})

async function load() {
  loading.value = true
  try {
    data.value = await getEthicsOverview()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.ethics-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.hero-card {
  border-radius: 12px;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0f9ff 100%);
}
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  h2 {
    margin: 0;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  p {
    color: #64748b;
    margin: 6px 0 0;
  }
  .hero-stat {
    text-align: center;
    .big {
      font-size: 56px;
      font-weight: 800;
      background: linear-gradient(135deg, #22c55e, #0ea5e9);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      line-height: 1;
    }
    .muted {
      color: #94a3b8;
      font-size: 12px;
      margin-top: 4px;
    }
  }
}
.principle-card {
  margin-bottom: 16px;
  border-radius: 10px;
  border-left: 3px solid #22c55e;
  .head {
    display: flex;
    align-items: center;
    gap: 8px;
    .title {
      flex: 1;
      font-weight: 700;
      color: #0f172a;
    }
  }
  .desc {
    margin-top: 8px;
    color: #475569;
    font-size: 13px;
    line-height: 1.6;
  }
}
.card-title {
  font-weight: 600;
}
.metric {
  text-align: center;
  padding: 12px 0;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 12px;
  .m-label {
    color: #64748b;
    font-size: 12px;
  }
  .m-value {
    margin-top: 4px;
    font-size: 26px;
    font-weight: 700;
    .m-unit {
      font-size: 12px;
      color: #94a3b8;
      margin-left: 4px;
    }
  }
}
.dict {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.dict-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  .kw {
    padding: 2px 8px;
    background: #fee2e2;
    color: #991b1b;
    border-radius: 4px;
    font-size: 12px;
    &.med {
      background: #fef3c7;
      color: #92400e;
    }
    &.low {
      background: #e0f2fe;
      color: #0369a1;
    }
  }
}
.prompt-block {
  background: #1e293b;
  color: #cbd5e1;
  padding: 12px;
  border-radius: 6px;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
}
.alert {
  margin-top: 8px;
}
.audit-card {
  margin-top: 16px;
}
.audit-row {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f1f5f9;
  .time {
    color: #94a3b8;
    font-size: 12px;
  }
  .detail {
    flex: 1;
    color: #475569;
    font-size: 13px;
  }
}
.empty {
  color: #94a3b8;
  text-align: center;
  padding: 12px;
}
.footer-note {
  ul {
    margin: 0;
    padding-left: 20px;
    li {
      padding: 6px 0;
      color: #475569;
    }
  }
}
</style>
