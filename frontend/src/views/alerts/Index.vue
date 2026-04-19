<template>
  <div class="alerts-page">
    <el-row :gutter="16">
      <el-col :xs="6" v-for="lv in levels" :key="lv.code">
        <el-card shadow="hover" class="level-card" :style="{ borderTop: `4px solid ${lv.color}` }">
          <div class="lv-label">{{ lv.label }}</div>
          <div class="lv-value" :style="{ color: lv.color }">{{ stats?.by_level[lv.code] || 0 }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <div class="head">
          <span class="card-title">预警列表</span>
          <div class="right">
            <el-select v-model="filterLevel" clearable placeholder="按级别筛选" style="width: 140px" @change="load">
              <el-option v-for="lv in levels" :key="lv.code" :label="lv.label" :value="lv.code" />
            </el-select>
            <el-select v-model="filterStatus" clearable placeholder="按状态筛选" style="width: 140px" @change="load">
              <el-option label="待处理" value="open" />
              <el-option label="已签收" value="acknowledged" />
              <el-option label="已处理" value="resolved" />
              <el-option label="已关闭" value="closed" />
            </el-select>
            <el-button type="primary" :loading="recomputing" @click="onRecompute">
              重新计算所有预警
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="levelTag(row.level)" effect="dark" size="small">
              {{ levelLabel(row.level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="评分" width="80">
          <template #default="{ row }">
            <strong :style="{ color: levelColor(row.level) }">{{ row.score.toFixed(0) }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="student_name" label="学生" width="120" />
        <el-table-column label="原因" min-width="280">
          <template #default="{ row }">
            <div v-for="(r, idx) in row.reasons" :key="idx" class="reason">· {{ r }}</div>
          </template>
        </el-table-column>
        <el-table-column label="数据来源" width="180">
          <template #default="{ row }">
            <el-tag v-for="s in row.sources" :key="s" size="small" effect="plain" class="src-tag">
              {{ s }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'open'" text type="primary" @click="onAck(row)">签收</el-button>
            <el-button
              v-if="row.status !== 'closed' && row.status !== 'resolved'"
              text
              type="success"
              @click="openResolve(row)"
            >处理</el-button>
            <el-button
              v-if="row.status !== 'closed'"
              text
              type="info"
              @click="openIntervention(row)"
            >干预记录</el-button>
            <el-button v-if="row.status !== 'closed'" text type="danger" @click="onClose(row)">关闭</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50]"
          layout="total, prev, pager, next"
          @current-change="load"
          @size-change="load"
        />
      </div>
    </el-card>

    <!-- 处理对话框 -->
    <el-dialog v-model="resolveVisible" title="处理预警" width="480px">
      <el-form label-width="80px">
        <el-form-item label="处理说明">
          <el-input v-model="resolveNote" type="textarea" :rows="4" placeholder="例：已与学生沟通..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resolveVisible = false">取消</el-button>
        <el-button type="primary" @click="onResolve">确认处理</el-button>
      </template>
    </el-dialog>

    <!-- 干预对话框 -->
    <el-dialog v-model="intervVisible" :title="`干预记录 · ${currentAlert?.student_name || ''}`" width="640px">
      <el-form label-width="100px">
        <el-form-item label="干预方式">
          <el-select v-model="interv.action" placeholder="选择">
            <el-option label="谈话" value="谈话" />
            <el-option label="家访" value="家访" />
            <el-option label="心理辅导" value="心理辅导" />
            <el-option label="转介医生" value="转介医生" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="干预内容">
          <el-input v-model="interv.summary" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="后续跟进">
          <el-input v-model="interv.follow_up" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <el-divider>历史记录</el-divider>
      <div v-if="!intervHistory.length" class="empty">暂无</div>
      <div v-for="r in intervHistory" :key="r.id" class="interv-row">
        <el-tag size="small">{{ r.action }}</el-tag>
        <div class="content">{{ r.summary }}</div>
        <div v-if="r.follow_up" class="follow">跟进：{{ r.follow_up }}</div>
        <div class="time">{{ r.created_at }}</div>
      </div>
      <template #footer>
        <el-button @click="intervVisible = false">关闭</el-button>
        <el-button type="primary" @click="onAddInterv">提交记录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import {
  ackAlert,
  addIntervention,
  closeAlert,
  getAlertStats,
  listAlerts,
  listInterventions,
  recomputeAlerts,
  resolveAlert,
  type AlertItem,
  type AlertStats,
} from '@/api/alerts'

const items = ref<AlertItem[]>([])
const stats = ref<AlertStats | null>(null)
const loading = ref(false)
const recomputing = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterLevel = ref('')
const filterStatus = ref('')

const resolveVisible = ref(false)
const resolveNote = ref('')
const intervVisible = ref(false)
const currentAlert = ref<AlertItem | null>(null)
const intervHistory = ref<any[]>([])
const interv = reactive({ action: '谈话', summary: '', follow_up: '' })

const levels = [
  { code: 'red', label: '紧急', color: '#ef4444' },
  { code: 'orange', label: '重点', color: '#f97316' },
  { code: 'yellow', label: '关注', color: '#f59e0b' },
  { code: 'green', label: '正常', color: '#22c55e' },
]

function levelTag(l: string): any {
  return { red: 'danger', orange: 'warning', yellow: 'warning', green: 'success' }[l] || 'info'
}
function levelLabel(l: string) {
  return { red: '紧急', orange: '重点', yellow: '关注', green: '正常' }[l] || l
}
function levelColor(l: string) {
  return { red: '#ef4444', orange: '#f97316', yellow: '#f59e0b', green: '#22c55e' }[l] || '#94a3b8'
}
function statusTag(s: string): any {
  return { open: 'danger', acknowledged: 'warning', resolved: 'success', closed: 'info' }[s] || 'info'
}
function statusLabel(s: string) {
  return { open: '待处理', acknowledged: '已签收', resolved: '已处理', closed: '已关闭' }[s] || s
}

async function load() {
  loading.value = true
  try {
    const data = await listAlerts({
      level: filterLevel.value || undefined,
      status: filterStatus.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    items.value = data.items
    total.value = data.total
    stats.value = await getAlertStats()
  } finally {
    loading.value = false
  }
}

async function onRecompute() {
  recomputing.value = true
  try {
    const r = await recomputeAlerts()
    ElMessage.success(`已处理 ${r.processed} 名学生，生成/更新 ${r.alerts_count} 条预警`)
    await load()
  } finally {
    recomputing.value = false
  }
}

async function onAck(row: AlertItem) {
  await ackAlert(row.id)
  ElMessage.success('已签收')
  await load()
}

function openResolve(row: AlertItem) {
  currentAlert.value = row
  resolveNote.value = ''
  resolveVisible.value = true
}
async function onResolve() {
  if (!currentAlert.value) return
  await resolveAlert(currentAlert.value.id, resolveNote.value)
  ElMessage.success('已处理')
  resolveVisible.value = false
  await load()
}

async function onClose(row: AlertItem) {
  await closeAlert(row.id)
  ElMessage.success('已关闭')
  await load()
}

async function openIntervention(row: AlertItem) {
  currentAlert.value = row
  intervHistory.value = (await listInterventions(row.id)).items
  Object.assign(interv, { action: '谈话', summary: '', follow_up: '' })
  intervVisible.value = true
}
async function onAddInterv() {
  if (!currentAlert.value || !interv.summary) {
    ElMessage.warning('请填写干预内容')
    return
  }
  await addIntervention(currentAlert.value.id, interv)
  ElMessage.success('已记录')
  intervHistory.value = (await listInterventions(currentAlert.value.id)).items
  Object.assign(interv, { action: '谈话', summary: '', follow_up: '' })
}

onMounted(load)
</script>

<style lang="scss" scoped>
.alerts-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.level-card {
  border-radius: 10px;
  text-align: center;
  padding: 6px 0;
  .lv-label {
    font-size: 13px;
    color: #64748b;
  }
  .lv-value {
    margin-top: 6px;
    font-size: 28px;
    font-weight: 700;
  }
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .card-title {
    font-weight: 600;
  }
  .right {
    display: flex;
    gap: 8px;
  }
}
.reason {
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
}
.src-tag {
  margin-right: 4px;
}
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
.empty {
  color: #94a3b8;
  text-align: center;
  padding: 12px;
}
.interv-row {
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
  .content {
    margin: 4px 0;
    color: #1f2937;
  }
  .follow {
    color: #0ea5e9;
    font-size: 12px;
  }
  .time {
    color: #94a3b8;
    font-size: 12px;
  }
}
</style>
