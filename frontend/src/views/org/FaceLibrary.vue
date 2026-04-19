<template>
  <div class="face-library">
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6" v-for="s in statItems" :key="s.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-value">
            {{ s.value }}<span class="unit">{{ s.unit }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never">
          <template #header>
            <div class="card-head">
              <span class="title">学生人脸列表</span>
              <div class="right">
                <el-select
                  v-model="classId"
                  filterable
                  clearable
                  style="width: 220px"
                  placeholder="选择班级"
                  @change="loadStudents"
                >
                  <el-option
                    v-for="c in classes"
                    :key="c.id"
                    :label="`${c.grade_name} · ${c.name}`"
                    :value="c.id"
                  />
                </el-select>
                <el-input
                  v-model="keyword"
                  style="width: 180px"
                  placeholder="按学号/姓名搜索"
                  clearable
                  @keyup.enter="loadStudents"
                />
                <el-button @click="loadStudents">查询</el-button>
              </div>
            </div>
          </template>
          <el-table
            :data="students"
            v-loading="loading"
            stripe
            size="small"
            highlight-current-row
            @current-change="onSelectStudent"
          >
            <el-table-column prop="student_no" label="学号" width="150" />
            <el-table-column prop="name" label="姓名" width="120" />
            <el-table-column prop="class_name" label="班级" width="120" />
            <el-table-column label="已注册" width="110">
              <template #default="{ row }">
                <el-tag
                  :type="(faceCountMap[row.id] || 0) > 0 ? 'success' : 'info'"
                  effect="plain"
                  size="small"
                >
                  {{ faceCountMap[row.id] || 0 }} 张
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination">
            <el-pagination
              v-model:current-page="page"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[15, 30, 60]"
              layout="total, sizes, prev, pager, next"
              @current-change="loadStudents"
              @size-change="loadStudents"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never">
          <template #header>
            <div class="card-head">
              <span class="title">
                <span v-if="selectedStudent">
                  {{ selectedStudent.name }} 的人脸（共 {{ studentFaces.length }} 张）
                </span>
                <span v-else>请从左侧选择一名学生</span>
              </span>
              <el-button
                v-if="userStore.isAdmin && selectedStudent"
                type="primary"
                :icon="UploadFilled"
                size="small"
                @click="triggerUpload"
              >
                注册人脸
              </el-button>
            </div>
          </template>
          <div v-if="!selectedStudent" class="placeholder">
            从左侧学生列表中选择一人，右侧显示其已注册的人脸
          </div>
          <div v-else>
            <el-upload
              ref="uploadRef"
              class="hidden-uploader"
              :show-file-list="false"
              :before-upload="beforeUpload"
              :auto-upload="false"
              accept="image/*"
              @change="onImageChange"
            >
              <div style="display: none"></div>
            </el-upload>

            <el-empty v-if="!studentFaces.length" description="尚未注册任何人脸" />
            <div v-else class="face-grid">
              <div v-for="f in studentFaces" :key="f.id" class="face-card">
                <img v-if="f.image_url" :src="resolveUrl(f.image_url)" class="face-img" />
                <div class="face-meta">
                  <div>置信度：{{ (f.confidence * 100).toFixed(1) }}%</div>
                  <div class="time">{{ f.created_at }}</div>
                </div>
                <el-button
                  v-if="userStore.isAdmin"
                  class="face-del"
                  text
                  type="danger"
                  size="small"
                  @click="onDelete(f)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="recognize-card">
          <template #header>
            <span class="title">人脸识别测试</span>
          </template>
          <el-upload
            class="recognize-upload"
            drag
            :show-file-list="false"
            :before-upload="beforeUpload"
            :auto-upload="false"
            accept="image/*"
            @change="onRecognizeImage"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">上传任意含人脸的图片，系统识别属于哪位已注册学生</div>
          </el-upload>
          <div v-if="recognizeResult" class="recognize-result">
            <div>检测到 {{ recognizeResult.count }} 张人脸，候选库 {{ recognizeResult.candidates || 0 }} 条</div>
            <div v-for="(r, idx) in recognizeResult.results" :key="idx" class="rec-item">
              <el-tag v-if="r.matched" type="success" effect="dark">
                命中：{{ r.student.name }}（{{ r.student.student_no }}）相似度
                {{ (r.score * 100).toFixed(1) }}%
              </el-tag>
              <el-tag v-else type="info">未匹配（最高相似度 {{ (r.score * 100).toFixed(1) }}%）</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

import {
  deleteFace,
  getFaceStats,
  getFacesByStudent,
  recognizeFace,
  registerFace,
  type FaceItem,
  type FaceStats,
} from '@/api/ai'
import { listClasses, listStudents, type Clazz, type Student } from '@/api/orgs'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const loading = ref(false)
const stats = ref<FaceStats | null>(null)
const classes = ref<Clazz[]>([])
const students = ref<Student[]>([])
const classId = ref<number>()
const keyword = ref('')
const page = ref(1)
const pageSize = ref(15)
const total = ref(0)
const faceCountMap = ref<Record<number, number>>({})

const selectedStudent = ref<Student | null>(null)
const studentFaces = ref<FaceItem[]>([])
const uploadRef = ref<any>()

const recognizeResult = ref<any>(null)

const statItems = computed(() => [
  { label: '已注册人脸', value: stats.value?.total_faces ?? 0, unit: '张' },
  { label: '已覆盖学生', value: stats.value?.registered_students ?? 0, unit: '人' },
  { label: '学生总数', value: stats.value?.total_students ?? 0, unit: '人' },
  { label: '覆盖率', value: stats.value?.coverage_percent ?? 0, unit: '%' },
])

function resolveUrl(url: string | null): string {
  if (!url) return ''
  if (url.startsWith('http') || url.startsWith('data:')) return url
  return url
}

async function loadStats() {
  stats.value = await getFaceStats()
}

async function loadOptions() {
  const c = await listClasses()
  classes.value = c.items
}

async function loadStudents() {
  loading.value = true
  try {
    const data = await listStudents({
      class_id: classId.value,
      keyword: keyword.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    students.value = data.items
    total.value = data.total
    await Promise.all(
      students.value.map(async (s) => {
        const { total: t } = await getFacesByStudent(s.id)
        faceCountMap.value[s.id] = t
      }),
    )
  } finally {
    loading.value = false
  }
}

async function onSelectStudent(s: Student | null) {
  selectedStudent.value = s
  if (!s) return
  const { items } = await getFacesByStudent(s.id)
  studentFaces.value = items
}

function triggerUpload() {
  const el = (uploadRef.value?.$el || uploadRef.value) as HTMLElement | undefined
  const input = el?.querySelector('input[type=file]') as HTMLInputElement | null
  input?.click()
}

function beforeUpload() {
  return false
}

async function onImageChange(file: any) {
  if (!selectedStudent.value) return
  const reader = new FileReader()
  reader.onload = async () => {
    const b64 = reader.result as string
    try {
      const r = await registerFace(selectedStudent.value!.id, b64)
      if (r.duplicated) {
        ElMessage.warning('该图片已注册过')
      } else {
        ElMessage.success('人脸注册成功')
      }
      await Promise.all([
        onSelectStudent(selectedStudent.value),
        loadStats(),
        loadStudents(),
      ])
    } catch (_) {
      // 错误已由拦截器弹出
    }
  }
  reader.readAsDataURL(file.raw)
}

async function onDelete(face: FaceItem) {
  await ElMessageBox.confirm('确定删除这张人脸？', '删除', { type: 'warning' })
  await deleteFace(face.id)
  ElMessage.success('已删除')
  await Promise.all([onSelectStudent(selectedStudent.value), loadStats(), loadStudents()])
}

async function onRecognizeImage(file: any) {
  const reader = new FileReader()
  reader.onload = async () => {
    const b64 = reader.result as string
    recognizeResult.value = await recognizeFace(b64)
  }
  reader.readAsDataURL(file.raw)
}

onMounted(async () => {
  await loadOptions()
  await loadStats()
  await loadStudents()
})
</script>

<style lang="scss" scoped>
.face-library {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-card {
  .stat-label {
    color: #64748b;
    font-size: 12px;
  }
  .stat-value {
    margin-top: 4px;
    font-size: 24px;
    font-weight: 700;
    color: #0f172a;
    .unit {
      font-size: 12px;
      color: #94a3b8;
      margin-left: 4px;
    }
  }
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  .title {
    font-weight: 600;
  }
  .right {
    display: flex;
    gap: 8px;
  }
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.placeholder {
  color: #94a3b8;
  text-align: center;
  padding: 40px 0;
}

.face-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.face-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px;
  position: relative;
  text-align: center;
}

.face-img {
  width: 100%;
  height: 120px;
  object-fit: cover;
  border-radius: 6px;
  background: #f1f5f9;
}

.face-meta {
  margin-top: 6px;
  font-size: 12px;
  color: #475569;
  .time {
    color: #94a3b8;
    margin-top: 2px;
  }
}

.face-del {
  position: absolute;
  top: 4px;
  right: 4px;
  padding: 2px 6px;
}

.recognize-card {
  margin-top: 16px;
}

.recognize-result {
  margin-top: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
  .rec-item {
    margin-top: 6px;
  }
}

.hidden-uploader {
  display: none;
}
</style>
