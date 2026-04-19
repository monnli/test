<template>
  <div class="reports-page">
    <el-card shadow="never">
      <template #header>
        <div class="head">
          <span class="card-title">报告中心</span>
          <div class="right">
            <el-select v-model="filterType" clearable placeholder="按类型" style="width: 160px" @change="load">
              <el-option label="班级周报" value="class" />
              <el-option label="学生档案" value="student" />
              <el-option label="学校综合" value="school" />
            </el-select>
            <el-button type="primary" @click="genVisible = true">生成新报告</el-button>
          </div>
        </div>
      </template>

      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="typeTag(row.type)" effect="dark" size="small">
              {{ typeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="280" />
        <el-table-column prop="target_name" label="对象" width="140" />
        <el-table-column prop="period" label="周期" width="120" />
        <el-table-column prop="summary" label="摘要" min-width="240" show-overflow-tooltip />
        <el-table-column prop="created_at" label="生成时间" width="170" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="onView(row)">查看</el-button>
            <el-button text type="success" @click="onDownload(row)">下载 PDF</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 生成对话框 -->
    <el-dialog v-model="genVisible" title="生成新报告" width="520px">
      <el-form label-width="100px">
        <el-form-item label="报告类型">
          <el-radio-group v-model="genType">
            <el-radio value="class">班级周报</el-radio>
            <el-radio value="student">学生档案</el-radio>
            <el-radio value="school">学校综合</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="genType === 'class'" label="选择班级">
          <el-select v-model="genTargetId" filterable placeholder="选择班级">
            <el-option v-for="c in classes" :key="c.id" :label="`${c.grade_name} · ${c.name}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="genType === 'student'" label="选择学生">
          <el-select
            v-model="genTargetId"
            filterable
            remote
            :remote-method="searchStudent"
            :loading="searching"
            placeholder="搜索学生"
          >
            <el-option v-for="s in studentOpts" :key="s.id" :label="`${s.name} （${s.student_no}）`" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="genVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="onGenerate">生成</el-button>
      </template>
    </el-dialog>

    <!-- 查看对话框 -->
    <el-dialog v-model="viewVisible" :title="currentReport?.title" width="800px">
      <div class="report-content" v-html="renderedContent" />
      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
        <el-button type="primary" @click="currentReport && onDownload(currentReport)">下载 PDF</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import {
  generateClassReport,
  generateSchoolReport,
  generateStudentReport,
  getReport,
  listReports,
  reportPdfUrl,
  type ReportItem,
} from '@/api/reports'
import { listClasses, listStudents, type Clazz, type Student } from '@/api/orgs'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const items = ref<ReportItem[]>([])
const loading = ref(false)
const filterType = ref('')
const genVisible = ref(false)
const generating = ref(false)
const genType = ref<'class' | 'student' | 'school'>('class')
const genTargetId = ref<number>()
const classes = ref<Clazz[]>([])
const studentOpts = ref<Student[]>([])
const searching = ref(false)

const viewVisible = ref(false)
const currentReport = ref<ReportItem | null>(null)

function typeTag(t: string): any {
  return { class: 'success', student: 'warning', school: 'primary' }[t] || 'info'
}
function typeLabel(t: string) {
  return { class: '班级周报', student: '学生档案', school: '学校综合' }[t] || t
}

async function load() {
  loading.value = true
  try {
    const data = await listReports({ type: filterType.value || undefined })
    items.value = data.items
  } finally {
    loading.value = false
  }
}

async function searchStudent(q: string) {
  if (!q) return
  searching.value = true
  try {
    studentOpts.value = (await listStudents({ keyword: q, page: 1, page_size: 30 })).items
  } finally {
    searching.value = false
  }
}

async function onGenerate() {
  generating.value = true
  try {
    let report: ReportItem
    if (genType.value === 'school') {
      report = await generateSchoolReport()
    } else if (genType.value === 'class') {
      if (!genTargetId.value) {
        ElMessage.warning('请选择班级')
        return
      }
      report = await generateClassReport(genTargetId.value)
    } else {
      if (!genTargetId.value) {
        ElMessage.warning('请选择学生')
        return
      }
      report = await generateStudentReport(genTargetId.value)
    }
    ElMessage.success('生成成功')
    genVisible.value = false
    await load()
    onView(report)
  } finally {
    generating.value = false
  }
}

async function onView(row: ReportItem) {
  currentReport.value = await getReport(row.id)
  viewVisible.value = true
}

const renderedContent = computed(() => {
  const md = currentReport.value?.content || ''
  // 极简 markdown 渲染
  return md
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^- (.*$)/gim, '<li>$1</li>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')
})

function onDownload(row: ReportItem) {
  const token = userStore.accessToken
  // 由于接口需要 Bearer，这里用 fetch 然后下载
  fetch(reportPdfUrl(row.id, String(Date.now())), {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((r) => r.blob())
    .then((b) => {
      const url = URL.createObjectURL(b)
      const a = document.createElement('a')
      a.href = url
      a.download = `${row.title}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    })
}

onMounted(async () => {
  classes.value = (await listClasses()).items
  await load()
})
</script>

<style lang="scss" scoped>
.reports-page {
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
  .right {
    display: flex;
    gap: 8px;
  }
}
.report-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 8px;
  line-height: 1.7;
  color: #1f2937;
  :deep(h1) { font-size: 22px; margin: 12px 0 6px; color: #0f172a; }
  :deep(h2) { font-size: 16px; margin: 16px 0 6px; color: #0f172a; border-left: 3px solid #22c55e; padding-left: 6px; }
  :deep(li) { margin-left: 18px; }
}
</style>
