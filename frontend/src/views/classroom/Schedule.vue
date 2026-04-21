<template>
  <el-card shadow="never">
    <template #header>
      <div class="head">
        <div>
          <span class="card-title">课表管理</span>
          <span class="muted">{{ filteredItems.length }} 条课表</span>
        </div>
        <div class="right">
          <el-select v-model="filterClass" placeholder="按班级筛选" clearable style="width: 200px" @change="load">
            <el-option
              v-for="c in classes"
              :key="c.id"
              :label="`${c.grade_name} · ${c.name}`"
              :value="c.id"
            />
          </el-select>
          <el-select v-model="filterWeekday" placeholder="按周次筛选" clearable style="width: 140px" @change="load">
            <el-option v-for="(d, i) in weekdays" :key="i + 1" :label="d" :value="i + 1" />
          </el-select>
          <el-button v-if="userStore.isAdmin" type="primary" :icon="Plus" @click="openDialog()">
            新增课程
          </el-button>
        </div>
      </div>
    </template>

    <!-- 周视图 -->
    <div class="week-grid" v-if="showWeekView">
      <div class="col-head">节次 \ 周</div>
      <div class="col-head" v-for="(d, i) in weekdays" :key="i">{{ d }}</div>

      <template v-for="p in periods" :key="p.period">
        <div class="row-head">{{ p.label }}</div>
        <div
          v-for="(d, i) in weekdays"
          :key="`${p.period}-${i}`"
          class="cell"
          :class="{ filled: getCell(i + 1, p.period) }"
        >
          <div v-if="getCell(i + 1, p.period)" class="item">
            <strong>{{ getCell(i + 1, p.period)?.subject_name }}</strong>
            <div class="t">{{ getCell(i + 1, p.period)?.teacher_name }}</div>
            <div class="c">{{ getCell(i + 1, p.period)?.class_name }}</div>
          </div>
        </div>
      </template>
    </div>

    <!-- 列表视图 -->
    <el-table :data="filteredItems" v-loading="loading" stripe size="small">
      <el-table-column prop="class_name" label="班级" />
      <el-table-column prop="subject_name" label="科目" width="100" />
      <el-table-column prop="teacher_name" label="教师" width="120" />
      <el-table-column label="周几" width="80">
        <template #default="{ row }">周{{ weekdayName(row.weekday) }}</template>
      </el-table-column>
      <el-table-column prop="period" label="节次" width="60" />
      <el-table-column label="时间" width="140">
        <template #default="{ row }">{{ row.start_time }} ~ {{ row.end_time }}</template>
      </el-table-column>
      <el-table-column label="生效期" width="240">
        <template #default="{ row }">{{ row.effective_from }} ~ {{ row.effective_to }}</template>
      </el-table-column>
      <el-table-column v-if="userStore.isAdmin" label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing?.id ? '编辑课程' : '新增课程'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="班级" prop="class_id">
          <el-select v-model="form.class_id" filterable placeholder="选择班级">
            <el-option
              v-for="c in classes"
              :key="c.id"
              :label="`${c.grade_name} · ${c.name}`"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="科目" prop="subject_id">
          <el-select v-model="form.subject_id" placeholder="选择科目">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="教师" prop="teacher_id">
          <el-select v-model="form.teacher_id" filterable placeholder="选择教师">
            <el-option
              v-for="t in teachers"
              :key="t.id"
              :label="`${t.name}（${t.teacher_no}）`"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="周几" prop="weekday">
          <el-select v-model="form.weekday">
            <el-option v-for="(d, i) in weekdays" :key="i + 1" :label="d" :value="i + 1" />
          </el-select>
        </el-form-item>
        <el-form-item label="节次" prop="period">
          <el-input-number v-model="form.period" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-time-picker v-model="startTimeObj" value-format="HH:mm" format="HH:mm" />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-time-picker v-model="endTimeObj" value-format="HH:mm" format="HH:mm" />
        </el-form-item>
        <el-form-item label="生效期" required>
          <el-date-picker
            v-model="effectiveRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
          />
        </el-form-item>
        <el-form-item v-if="conflicts.length" label="冲突检测">
          <el-alert v-for="(c, i) in conflicts" :key="i" :title="c" type="error" :closable="false" class="conflict" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="conflicts.length > 0" @click="onSubmit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

import {
  checkScheduleConflict,
  createSchedule,
  deleteSchedule,
  listSchedules,
  updateSchedule,
  type Schedule,
} from '@/api/m10'
import { listClasses, listSubjects, listTeachers, type Clazz, type Subject, type Teacher } from '@/api/orgs'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const items = ref<Schedule[]>([])
const classes = ref<Clazz[]>([])
const subjects = ref<Subject[]>([])
const teachers = ref<Teacher[]>([])
const loading = ref(false)
const filterClass = ref<number>()
const filterWeekday = ref<number>()

const weekdays = ['一', '二', '三', '四', '五', '六', '日']
const periods = [
  { period: 1, label: '第1节' },
  { period: 2, label: '第2节' },
  { period: 3, label: '第3节' },
  { period: 4, label: '第4节' },
  { period: 5, label: '第5节' },
]

const dialogVisible = ref(false)
const submitting = ref(false)
const editing = ref<Schedule | null>(null)
const formRef = ref<FormInstance>()
const conflicts = ref<string[]>([])

const form = reactive({
  class_id: undefined as number | undefined,
  subject_id: undefined as number | undefined,
  teacher_id: undefined as number | undefined,
  weekday: 1,
  period: 1,
  start_time: '08:00',
  end_time: '08:45',
  effective_from: '2026-02-17',
  effective_to: '2026-07-05',
  note: '',
})

const startTimeObj = ref<string>('08:00')
const endTimeObj = ref<string>('08:45')
const effectiveRange = ref<[string, string]>(['2026-02-17', '2026-07-05'])

watch(startTimeObj, (v) => { form.start_time = v || '08:00' })
watch(endTimeObj, (v) => { form.end_time = v || '08:45' })
watch(effectiveRange, (v) => {
  if (v) {
    form.effective_from = v[0]
    form.effective_to = v[1]
  }
})

const rules: FormRules = {
  class_id: [{ required: true, message: '请选择班级', trigger: 'change' }],
  subject_id: [{ required: true, message: '请选择科目', trigger: 'change' }],
  teacher_id: [{ required: true, message: '请选择教师', trigger: 'change' }],
}

const filteredItems = computed(() => {
  let arr = items.value
  if (filterClass.value) arr = arr.filter((i) => i.class_id === filterClass.value)
  if (filterWeekday.value) arr = arr.filter((i) => i.weekday === filterWeekday.value)
  return arr
})

const showWeekView = computed(() => filterClass.value != null)

function getCell(weekday: number, period: number): Schedule | undefined {
  return filteredItems.value.find((i) => i.weekday === weekday && i.period === period)
}

function weekdayName(n: number) {
  return weekdays[n - 1] || '?'
}

async function loadOpts() {
  const [c, s, t] = await Promise.all([listClasses(), listSubjects(), listTeachers()])
  classes.value = c.items
  subjects.value = s.items
  teachers.value = t.items
}

async function load() {
  loading.value = true
  try {
    items.value = (await listSchedules()).items
  } finally {
    loading.value = false
  }
}

function openDialog(row?: Schedule) {
  editing.value = row || null
  Object.assign(form, {
    class_id: row?.class_id,
    subject_id: row?.subject_id,
    teacher_id: row?.teacher_id,
    weekday: row?.weekday || 1,
    period: row?.period || 1,
    start_time: row?.start_time || '08:00',
    end_time: row?.end_time || '08:45',
    effective_from: row?.effective_from || '2026-02-17',
    effective_to: row?.effective_to || '2026-07-05',
    note: row?.note || '',
  })
  startTimeObj.value = form.start_time
  endTimeObj.value = form.end_time
  effectiveRange.value = [form.effective_from, form.effective_to]
  conflicts.value = []
  dialogVisible.value = true
}

watch(
  () => ({ ...form }),
  async (v) => {
    if (!dialogVisible.value) return
    if (!v.class_id || !v.teacher_id || !v.subject_id) {
      conflicts.value = []
      return
    }
    try {
      const r = await checkScheduleConflict({ ...v })
      conflicts.value = r.conflicts
    } catch {
      conflicts.value = []
    }
  },
  { deep: true, immediate: false },
)

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (editing.value?.id) {
        await updateSchedule(editing.value.id, form)
      } else {
        await createSchedule(form)
      }
      ElMessage.success('已保存')
      dialogVisible.value = false
      await load()
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row: Schedule) {
  await ElMessageBox.confirm('确定删除这条课程？', '删除', { type: 'warning' })
  await deleteSchedule(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(async () => {
  await loadOpts()
  await load()
})
</script>

<style lang="scss" scoped>
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
    gap: 8px;
  }
}
.week-grid {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  .col-head,
  .row-head {
    background: #f1f5f9;
    padding: 8px;
    font-weight: 600;
    text-align: center;
    color: #0f172a;
    font-size: 13px;
  }
  .cell {
    min-height: 70px;
    padding: 6px;
    border-left: 1px solid #f1f5f9;
    border-top: 1px solid #f1f5f9;
    font-size: 12px;
    &.filled {
      background: linear-gradient(135deg, #ecfdf5, #f0f9ff);
    }
    .item {
      strong {
        color: #0f172a;
      }
      .t {
        color: #0ea5e9;
        margin-top: 2px;
      }
      .c {
        color: #94a3b8;
      }
    }
  }
}
.conflict {
  margin-bottom: 4px;
}
</style>
