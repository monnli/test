<template>
  <div class="home-page">
    <header class="topbar">
      <div class="brand">
        <span class="logo-dot" />
        <span class="brand-name">青苗守护者</span>
        <el-tag size="small" effect="plain" round type="success">M0 · 基础设施</el-tag>
      </div>
      <div class="actions">
        <el-button text @click="onLogout">
          <el-icon><SwitchButton /></el-icon>
          退出
        </el-button>
      </div>
    </header>

    <main class="content">
      <h2 class="page-title">系统初始化已完成</h2>
      <p class="page-desc">
        当前位于 M0 阶段。后端、前端、AI 服务的最小可运行链路已就绪。下面是依赖服务的实时状态：
      </p>

      <el-row :gutter="20" class="cards">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in services" :key="item.key">
          <el-card shadow="hover" class="status-card">
            <div class="card-head">
              <el-icon :size="20" :color="item.color"><component :is="item.icon" /></el-icon>
              <span class="name">{{ item.name }}</span>
            </div>
            <div class="status">
              <el-tag :type="statusOf(item.key).tagType" effect="dark" round>
                {{ statusOf(item.key).label }}
              </el-tag>
            </div>
            <div class="detail" v-if="statusOf(item.key).detail">
              {{ statusOf(item.key).detail }}
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="roadmap">
        <template #header>
          <div class="roadmap-head">
            <span>开发路线图</span>
            <el-button size="small" :loading="loading" @click="loadHealth">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
        </template>
        <el-steps :active="1" finish-status="success" align-center>
          <el-step title="M0" description="基础设施" />
          <el-step title="M1" description="用户与权限" />
          <el-step title="M2" description="AI 推理服务" />
          <el-step title="M3" description="课堂视频分析" />
          <el-step title="M4" description="心理健康" />
          <el-step title="M5" description="关联与预警" />
          <el-step title="M6" description="数据大屏" />
          <el-step title="M7" description="报告中心" />
          <el-step title="M8" description="演示打磨" />
        </el-steps>
      </el-card>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Cpu,
  Coin,
  DataLine,
  Monitor,
  Refresh,
  SwitchButton,
} from '@element-plus/icons-vue'

import { getDeepHealth } from '@/api/system'

const router = useRouter()
const loading = ref(false)

const services = [
  { key: 'backend', name: 'Flask 后端', icon: Monitor, color: '#0ea5e9' },
  { key: 'mysql', name: 'MySQL', icon: DataLine, color: '#22c55e' },
  { key: 'redis', name: 'Redis', icon: Coin, color: '#ef4444' },
  { key: 'minio', name: 'MinIO', icon: Coin, color: '#a855f7' },
  { key: 'ai_service', name: 'AI 推理服务', icon: Cpu, color: '#f97316' },
] as const

type StatusInfo = { label: string; tagType: 'success' | 'danger' | 'info'; detail?: string }
const statuses = reactive<Record<string, StatusInfo>>({
  backend: { label: '检测中…', tagType: 'info' },
  mysql: { label: '检测中…', tagType: 'info' },
  redis: { label: '检测中…', tagType: 'info' },
  minio: { label: '检测中…', tagType: 'info' },
  ai_service: { label: '检测中…', tagType: 'info' },
})

function statusOf(key: string): StatusInfo {
  return statuses[key] || { label: '未知', tagType: 'info' }
}

async function loadHealth() {
  loading.value = true
  statuses.backend = { label: '已连通', tagType: 'success' }
  try {
    const data: any = await getDeepHealth()
    const deps = data?.dependencies || data?.data?.dependencies || {}
    for (const key of Object.keys(deps)) {
      const dep = deps[key]
      statuses[key] = dep.status === 'ok'
        ? { label: '正常', tagType: 'success' }
        : { label: '异常', tagType: 'danger', detail: dep.detail }
    }
  } catch {
    statuses.backend = { label: '后端不可达', tagType: 'danger' }
  } finally {
    loading.value = false
  }
}

function onLogout() {
  localStorage.removeItem('access_token')
  router.push('/login')
}

onMounted(loadHealth)
</script>

<style lang="scss" scoped>
.home-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 24px;
  background: #fff;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.06);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-dot {
  width: 10px;
  height: 10px;
  background: linear-gradient(135deg, #22c55e, #0ea5e9);
  border-radius: 50%;
}

.brand-name {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 1px;
}

.content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px;
}

.page-title {
  margin: 8px 0 4px;
  color: #0f172a;
}

.page-desc {
  margin: 0 0 20px;
  color: #64748b;
}

.cards {
  margin-bottom: 24px;
}

.status-card {
  border-radius: 10px;

  .card-head {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 12px;
  }

  .status {
    margin-bottom: 6px;
  }

  .detail {
    font-size: 12px;
    color: #94a3b8;
    word-break: break-all;
  }
}

.roadmap {
  border-radius: 10px;

  .roadmap-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 600;
  }
}
</style>
