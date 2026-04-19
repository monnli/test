<template>
  <div class="psy-home">
    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never">
          <template #header>
            <div class="head">
              <span class="card-title">标准化心理量表</span>
              <el-button size="small" type="primary" :loading="seeding" @click="onSeed">
                初始化量表
              </el-button>
            </div>
          </template>
          <el-table :data="scales" stripe v-loading="loading">
            <el-table-column prop="code" label="编码" width="100" />
            <el-table-column prop="name" label="量表名称" min-width="200" />
            <el-table-column prop="target" label="评估目标" width="160" />
            <el-table-column prop="question_count" label="题数" width="80" />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button text type="primary" @click="openAssessDialog(row)">下发测评</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card shadow="never">
          <template #header><span class="card-title">学生心理档案入口</span></template>
          <div class="search-area">
            <el-select
              v-model="selectedStudentId"
              filterable
              remote
              :remote-method="searchStudent"
              :loading="searching"
              placeholder="搜索学生姓名/学号"
              style="width: 100%"
            >
              <el-option
                v-for="s in studentOptions"
                :key="s.id"
                :label="`${s.name} （${s.student_no}）`"
                :value="s.id"
              />
            </el-select>
            <el-button
              type="primary"
              :disabled="!selectedStudentId"
              @click="openProfile"
              style="margin-top: 12px; width: 100%"
            >
              进入档案
            </el-button>
          </div>
          <el-divider>最近测评</el-divider>
          <div v-if="!recentAssessments.length" class="empty">暂无</div>
          <div v-for="a in recentAssessments" :key="a.id" class="assess-row">
            <el-tag :type="levelTagType(a.level_color)" effect="dark" size="small">{{ a.level }}</el-tag>
            <span class="grow">{{ a.student_name }} · {{ a.scale_code }}</span>
            <span class="score">{{ a.total_score.toFixed(0) }}</span>
            <el-button text size="small" @click="$router.push(`/psychology/student/${a.student_id}`)">
              档案
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 测评对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="`下发测评 · ${currentScale?.name || ''}`"
      width="720px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px" v-if="currentScaleDetail">
        <el-form-item label="选择学生">
          <el-select
            v-model="selectedStudentId"
            filterable
            remote
            :remote-method="searchStudent"
            :loading="searching"
            placeholder="搜索学生姓名/学号"
            style="width: 100%"
          >
            <el-option
              v-for="s in studentOptions"
              :key="s.id"
              :label="`${s.name} （${s.student_no}）`"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <div class="quiz" v-if="currentScaleDetail">
        <div v-for="q in currentScaleDetail.questions" :key="q.id" class="quiz-item">
          <div class="q-content">{{ q.sort_order + 1 }}. {{ q.content }}</div>
          <el-radio-group v-model="answers[q.id]">
            <el-radio
              v-for="opt in q.options"
              :key="opt.label"
              :value="opt.score"
              border
              size="small"
            >
              {{ opt.label }}
            </el-radio>
          </el-radio-group>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="onSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  getScale,
  listAssessments,
  listScales,
  seedScales,
  submitAssessment,
  type AssessmentItem,
  type Scale,
  type ScaleDetail,
} from '@/api/psychology'
import { listStudents, type Student } from '@/api/orgs'

const router = useRouter()
const loading = ref(false)
const seeding = ref(false)
const submitting = ref(false)
const scales = ref<Scale[]>([])
const recentAssessments = ref<AssessmentItem[]>([])

const currentScale = ref<Scale | null>(null)
const currentScaleDetail = ref<ScaleDetail | null>(null)
const dialogVisible = ref(false)
const answers = reactive<Record<number, number>>({})

const selectedStudentId = ref<number>()
const studentOptions = ref<Student[]>([])
const searching = ref(false)

function levelTagType(color: string): any {
  return (
    { green: 'success', blue: 'info', orange: 'warning', red: 'danger', purple: 'danger', gray: 'info' }[color] ||
    'info'
  )
}

async function load() {
  loading.value = true
  try {
    scales.value = (await listScales()).items
    recentAssessments.value = (await listAssessments({ })).items.slice(0, 8)
  } finally {
    loading.value = false
  }
}

async function onSeed() {
  seeding.value = true
  try {
    await seedScales()
    ElMessage.success('量表已初始化')
    await load()
  } finally {
    seeding.value = false
  }
}

async function searchStudent(q: string) {
  if (!q) return
  searching.value = true
  try {
    const r = await listStudents({ keyword: q, page: 1, page_size: 30 })
    studentOptions.value = r.items
  } finally {
    searching.value = false
  }
}

async function openAssessDialog(scale: Scale) {
  currentScale.value = scale
  currentScaleDetail.value = await getScale(scale.id)
  Object.keys(answers).forEach((k) => delete answers[+k])
  currentScaleDetail.value.questions.forEach((q) => {
    answers[q.id] = q.options[0]?.score ?? 0
  })
  dialogVisible.value = true
}

async function onSubmit() {
  if (!selectedStudentId.value) {
    ElMessage.warning('请选择学生')
    return
  }
  if (!currentScaleDetail.value) return
  submitting.value = true
  try {
    const result = await submitAssessment({
      student_id: selectedStudentId.value,
      scale_id: currentScaleDetail.value.id,
      answers,
    })
    ElMessage.success(`提交成功 · 评级：${result.level}`)
    dialogVisible.value = false
    await ElMessageBox.confirm(
      `${result.level}（建议：${result.advice}）。是否查看该学生档案？`,
      '完成',
      { type: 'success' },
    )
      .then(() => router.push(`/psychology/student/${result.student_id}`))
      .catch(() => {})
    await load()
  } finally {
    submitting.value = false
  }
}

function openProfile() {
  if (selectedStudentId.value) {
    router.push(`/psychology/student/${selectedStudentId.value}`)
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.psy-home {
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
.search-area {
  padding: 8px 0;
}
.empty {
  color: #94a3b8;
  text-align: center;
  padding: 16px 0;
}
.assess-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #f1f5f9;
  .grow {
    flex: 1;
    color: #1f2937;
    font-size: 13px;
  }
  .score {
    color: #ef4444;
    font-weight: 700;
  }
}
.quiz {
  max-height: 50vh;
  overflow-y: auto;
  padding-right: 8px;
}
.quiz-item {
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #e5e7eb;
  .q-content {
    margin-bottom: 8px;
    font-weight: 500;
    color: #0f172a;
  }
}
</style>
