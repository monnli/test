<template>
  <div v-if="active" class="demo-banner">
    <div class="bar">
      <el-icon class="rotate"><VideoPlay /></el-icon>
      <span class="title">演示模式</span>
      <span class="step">{{ currentIdx + 1 }} / {{ steps.length }}</span>
      <span class="narrate">{{ currentNarrate }}</span>
      <el-progress :percentage="progressPct" :show-text="false" :stroke-width="3" class="progress" />
      <el-button text @click="prev" :disabled="currentIdx <= 0">上一步</el-button>
      <el-button text @click="next">下一步</el-button>
      <el-button text @click="stop">退出 (Esc)</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'

import { getDemoScript, type DemoStep } from '@/api/enhance'

const router = useRouter()
const active = ref(false)
const steps = ref<DemoStep[]>([])
const currentIdx = ref(0)
const elapsed = ref(0)
let mainTimer: any
let progressTimer: any

const currentNarrate = computed(() => steps.value[currentIdx.value]?.narrate || '')
const progressPct = computed(() => {
  const total = steps.value[currentIdx.value]?.duration || 1
  return Math.min(100, Math.round((elapsed.value / total) * 100))
})

async function start() {
  if (active.value) return
  try {
    const r = await getDemoScript()
    steps.value = r.steps
  } catch {
    ElMessage.error('无法加载演示脚本')
    return
  }
  if (!steps.value.length) return
  active.value = true
  currentIdx.value = 0
  ElMessage.success('演示模式已启动 · 按 Esc 退出')
  goTo(0)
}

function stop() {
  active.value = false
  if (mainTimer) clearTimeout(mainTimer)
  if (progressTimer) clearInterval(progressTimer)
  ElMessage.info('演示模式已退出')
}

function goTo(idx: number) {
  if (idx < 0 || idx >= steps.value.length) {
    stop()
    return
  }
  currentIdx.value = idx
  elapsed.value = 0
  const step = steps.value[idx]
  router.push(step.path).catch(() => {})

  if (mainTimer) clearTimeout(mainTimer)
  if (progressTimer) clearInterval(progressTimer)
  progressTimer = setInterval(() => {
    elapsed.value += 100
  }, 100)
  mainTimer = setTimeout(() => {
    next()
  }, step.duration)
}

function next() {
  if (currentIdx.value >= steps.value.length - 1) {
    // 循环
    goTo(0)
  } else {
    goTo(currentIdx.value + 1)
  }
}

function prev() {
  goTo(Math.max(0, currentIdx.value - 1))
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'F9') {
    e.preventDefault()
    if (active.value) {
      stop()
    } else {
      start()
    }
  } else if (e.key === 'Escape' && active.value) {
    stop()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKey)
  // 暴露全局方法方便手动调试
  ;(window as any).__demoStart = start
  ;(window as any).__demoStop = stop
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  if (mainTimer) clearTimeout(mainTimer)
  if (progressTimer) clearInterval(progressTimer)
})

// 暴露给父组件
defineExpose({ start, stop, toggle: () => (active.value ? stop() : start()) })
</script>

<style lang="scss" scoped>
.demo-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 99999;
  pointer-events: auto;
}
.bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: linear-gradient(90deg, rgba(34, 197, 94, 0.95), rgba(14, 165, 233, 0.95));
  color: #fff;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  .title {
    font-weight: 700;
    letter-spacing: 1px;
  }
  .step {
    color: rgba(255, 255, 255, 0.8);
  }
  .narrate {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .progress {
    width: 200px;
  }
  .el-button {
    color: #fff !important;
  }
}
.rotate {
  animation: spin 2s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
