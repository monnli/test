<template>
  <div v-if="active" class="demo-banner">
    <div class="bar" :class="{ paused: isPaused }">
      <el-icon class="rotate" :class="{ 'is-paused': isPaused }"><VideoPlay /></el-icon>
      <span class="title">演示模式</span>
      <el-tag v-if="isPaused" type="warning" effect="dark" size="small">已暂停</el-tag>
      <span class="step">{{ currentIdx + 1 }} / {{ steps.length }}</span>
      <span class="narrate" :title="currentNarrate">{{ currentNarrate }}</span>
      <el-progress :percentage="progressPct" :show-text="false" :stroke-width="3" class="progress" />
      <el-button text @click="togglePause">
        {{ isPaused ? '继续' : '暂停' }}
      </el-button>
      <el-button text @click="prev" :disabled="currentIdx <= 0">上一步</el-button>
      <el-button text @click="next">下一步</el-button>
      <el-button text @click="stop">退出 (Esc)</el-button>
    </div>
    <div class="hint">F9 开/关演示 · 空格 暂停/继续 · 口播可悬停看全文</div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'

import { getDemoScript, type DemoStep } from '@/api/enhance'

const router = useRouter()
const active = ref(false)
const steps = ref<DemoStep[]>([])
const currentIdx = ref(0)
const elapsed = ref(0)
const isPaused = ref(false)
let mainTimer: ReturnType<typeof setTimeout> | undefined
let progressTimer: ReturnType<typeof setInterval> | undefined
let scrollRafId = 0
let scrollGen = 0

function easeInOutQuad(t: number) {
  return t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2
}

/** 演示页主滚动区：主布局下为 el-main；否则用文档滚动根 */
function getDemoScrollRoot(): HTMLElement | null {
  const main = document.querySelector('.main-layout .el-main.main-content') as HTMLElement | null
  if (main && main.scrollHeight > main.clientHeight + 2) return main
  const docEl = document.scrollingElement as HTMLElement | null
  if (docEl && docEl.scrollHeight > docEl.clientHeight + 2) return docEl
  return main || docEl
}

function cancelPageScroll() {
  scrollGen++
  if (scrollRafId) {
    cancelAnimationFrame(scrollRafId)
    scrollRafId = 0
  }
}

/** 本步停留时间内：长页自动从顶滚到底再回顶，便于看全内容 */
function runDemoPageScroll(durationMs: number) {
  cancelPageScroll()
  const myGen = scrollGen
  const root = getDemoScrollRoot()
  if (!root || !active.value) return
  const maxY = Math.max(0, root.scrollHeight - root.clientHeight)
  if (maxY <= 2) {
    root.scrollTop = 0
    return
  }
  root.scrollTop = 0
  const t0 = performance.now()
  const dwellTop = 0.08
  const goDown = 0.52
  const goUp = 0.28

  const tick = (now: number) => {
    scrollRafId = 0
    if (!active.value || myGen !== scrollGen) return
    if (isPaused.value) return

    const u = Math.min(1, (now - t0) / Math.max(800, durationMs))
    let frac = 0
    if (u < dwellTop) frac = 0
    else if (u < dwellTop + goDown) {
      const w = (u - dwellTop) / goDown
      frac = easeInOutQuad(w)
    } else if (u < dwellTop + goDown + goUp) {
      const w = (u - dwellTop - goDown) / goUp
      frac = easeInOutQuad(1 - w)
    } else frac = 0

    root.scrollTop = frac * maxY

    if (u < 1 && active.value && !isPaused.value) {
      scrollRafId = requestAnimationFrame(tick)
    }
  }
  scrollRafId = requestAnimationFrame(tick)
}

const currentNarrate = computed(() => steps.value[currentIdx.value]?.narrate || '')
const progressPct = computed(() => {
  const total = steps.value[currentIdx.value]?.duration || 1
  return Math.min(100, Math.round((elapsed.value / total) * 100))
})

function clearTimers() {
  cancelPageScroll()
  if (mainTimer !== undefined) {
    clearTimeout(mainTimer)
    mainTimer = undefined
  }
  if (progressTimer !== undefined) {
    clearInterval(progressTimer)
    progressTimer = undefined
  }
}

function scheduleStepTimers(durationMs: number) {
  clearTimers()
  progressTimer = setInterval(() => {
    if (!isPaused.value) elapsed.value += 100
  }, 100)
  mainTimer = setTimeout(() => {
    next()
  }, durationMs)
}

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
  isPaused.value = false
  currentIdx.value = 0
  ElMessage.success('演示模式已启动 · F9 退出/再开 · 空格暂停 · Esc 退出')
  void goTo(0)
}

function stop() {
  active.value = false
  isPaused.value = false
  clearTimers()
  ElMessage.info('演示模式已退出')
}

async function goTo(idx: number) {
  if (idx < 0 || idx >= steps.value.length) {
    stop()
    return
  }
  isPaused.value = false
  currentIdx.value = idx
  elapsed.value = 0
  const step = steps.value[idx]

  clearTimers()
  scheduleStepTimers(step.duration)

  await router.push(step.path).catch(() => {})
  await nextTick()
  await new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()))
  })
  runDemoPageScroll(step.duration)
}

function togglePause() {
  if (!active.value) return
  if (isPaused.value) {
    resume()
  } else {
    pause()
  }
}

function pause() {
  if (!active.value || isPaused.value) return
  isPaused.value = true
  clearTimers()
}

function resume() {
  if (!active.value || !isPaused.value) return
  const step = steps.value[currentIdx.value]
  if (!step) return
  isPaused.value = false
  const remaining = Math.max(400, step.duration - elapsed.value)
  progressTimer = setInterval(() => {
    elapsed.value += 100
  }, 100)
  mainTimer = setTimeout(() => {
    next()
  }, remaining)
}

function next() {
  if (currentIdx.value >= steps.value.length - 1) {
    void goTo(0)
  } else {
    void goTo(currentIdx.value + 1)
  }
}

function prev() {
  void goTo(Math.max(0, currentIdx.value - 1))
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'F9') {
    e.preventDefault()
    if (active.value) {
      stop()
    } else {
      void start()
    }
    return
  }
  if (e.key === 'Escape' && active.value) {
    stop()
    return
  }
  if (e.key === ' ' && active.value) {
    const t = e.target as HTMLElement | null
    if (t) {
      const tag = t.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || t.isContentEditable) return
    }
    e.preventDefault()
    togglePause()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKey)
  ;(window as any).__demoStart = start
  ;(window as any).__demoStop = stop
  ;(window as any).__demoTogglePause = togglePause
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  clearTimers()
})

defineExpose({
  start,
  stop,
  toggle: () => (active.value ? stop() : start()),
  togglePause,
})
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
  align-items: flex-start;
  gap: 10px;
  padding: 10px 16px 8px;
  background: linear-gradient(90deg, rgba(34, 197, 94, 0.95), rgba(14, 165, 233, 0.95));
  color: #fff;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  flex-wrap: wrap;

  &.paused {
    background: linear-gradient(90deg, rgba(100, 116, 139, 0.95), rgba(71, 85, 105, 0.95));
  }

  .title {
    font-weight: 700;
    letter-spacing: 1px;
    line-height: 1.4;
  }
  .step {
    color: rgba(255, 255, 255, 0.85);
    line-height: 1.4;
    white-space: nowrap;
  }
  .narrate {
    flex: 1;
    min-width: 200px;
    min-height: 2.6em;
    line-height: 1.45;
    max-height: 4.4em;
    overflow: hidden;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
    white-space: normal;
    color: rgba(255, 255, 255, 0.95);
  }
  .progress {
    width: min(200px, 18vw);
    align-self: center;
  }
  .el-button {
    color: #fff !important;
    align-self: center;
  }
}
.hint {
  padding: 4px 16px 6px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(15, 23, 42, 0.88);
  border-bottom: 1px solid rgba(148, 163, 184, 0.25);
}
.rotate {
  animation: spin 2s linear infinite;
  flex-shrink: 0;
  margin-top: 2px;
}
.rotate.is-paused {
  animation: none;
  opacity: 0.75;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
