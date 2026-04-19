<template>
  <div class="login-page">
    <div class="bg-grid" />
    <div class="login-card">
      <div class="brand">
        <div class="logo">
          <svg viewBox="0 0 64 64" width="48" height="48">
            <defs>
              <linearGradient id="lg" x1="0" x2="1" y1="0" y2="1">
                <stop offset="0" stop-color="#22c55e" />
                <stop offset="1" stop-color="#0ea5e9" />
              </linearGradient>
            </defs>
            <rect width="64" height="64" rx="14" fill="url(#lg)" />
            <path
              d="M32 14c-9 0-16 6-16 14 0 6 4 11 10 13v9h12v-9c6-2 10-7 10-13 0-8-7-14-16-14z"
              fill="#fff"
            />
          </svg>
        </div>
        <div class="title-area">
          <div class="title">青苗守护者</div>
          <div class="subtitle">AI 中小学生课堂行为与心理健康综合分析平台</div>
        </div>
      </div>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-position="top"
        size="large"
        class="login-form"
        @submit.prevent="onSubmit"
      >
        <el-form-item label="账号" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入账号"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            show-password
            placeholder="请输入密码"
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-button
          type="primary"
          class="submit-btn"
          :loading="loading"
          @click="onSubmit"
        >
          登 录
        </el-button>
      </el-form>

      <el-divider>系统状态</el-divider>

      <div class="health-block">
        <el-tag :type="healthTagType" effect="dark" round>
          {{ healthLabel }}
        </el-tag>
        <el-button text type="primary" :loading="checking" @click="checkHealth">
          <el-icon><Refresh /></el-icon>
          重新检测
        </el-button>
      </div>

      <div class="footer">
        <span>负责任的 AI · 守护每一株青苗</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Lock, Refresh, User } from '@element-plus/icons-vue'

import { getHealth } from '@/api/system'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const checking = ref(false)
const healthLabel = ref('未检测')
const healthTagType = ref<'success' | 'danger' | 'info' | 'warning'>('info')

const formData = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      // M0 阶段：登录接口尚未实现，模拟成功后跳转首页
      ElMessage.success('M0 阶段：用户系统将在 M1 中实现，先跳转到首页演示')
      localStorage.setItem('access_token', 'demo-token')
      router.push('/home')
    } finally {
      loading.value = false
    }
  })
}

async function checkHealth() {
  checking.value = true
  try {
    const data = await getHealth()
    if (data?.status === 'healthy') {
      healthLabel.value = `后端服务正常 · ${data.service}`
      healthTagType.value = 'success'
    } else {
      healthLabel.value = '后端服务异常'
      healthTagType.value = 'danger'
    }
  } catch {
    healthLabel.value = '后端连接失败'
    healthTagType.value = 'danger'
  } finally {
    checking.value = false
  }
}

onMounted(checkHealth)
</script>

<style lang="scss" scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at top, #1e293b 0%, #020617 70%);
  overflow: hidden;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(14, 165, 233, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(14, 165, 233, 0.08) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse at center, black 40%, transparent 80%);
  pointer-events: none;
}

.login-card {
  position: relative;
  width: 420px;
  padding: 40px 36px 28px;
  background: rgba(255, 255, 255, 0.96);
  border-radius: 16px;
  box-shadow:
    0 20px 60px rgba(2, 6, 23, 0.6),
    0 0 0 1px rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.title {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 1px;
}

.subtitle {
  margin-top: 2px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.login-form {
  :deep(.el-form-item__label) {
    color: #334155;
    font-weight: 500;
  }
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  letter-spacing: 6px;
  background: linear-gradient(90deg, #22c55e, #0ea5e9);
  border: none;
  margin-top: 6px;
}

.health-block {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 4px 0;
}

.footer {
  margin-top: 18px;
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  letter-spacing: 1px;
}
</style>
