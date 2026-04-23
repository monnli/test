<template>
  <DemoMode ref="demoRef" />
  <el-container class="main-layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="aside">
      <div class="brand" :class="{ collapsed }">
        <span class="logo-dot" />
        <span v-if="!collapsed" class="brand-name">青苗守护者</span>
      </div>
      <el-scrollbar class="menu-scroll">
        <el-menu
          :default-active="activeMenu"
          :collapse="collapsed"
          :collapse-transition="false"
          background-color="#0f172a"
          text-color="#cbd5e1"
          active-text-color="#22d3ee"
          router
        >
          <template v-for="item in visibleMenu" :key="item.path">
            <el-sub-menu v-if="item.children" :index="item.path">
              <template #title>
                <el-icon><component :is="item.icon" /></el-icon>
                <span>{{ item.title }}</span>
              </template>
              <el-menu-item
                v-for="child in item.children"
                :key="child.path"
                :index="child.path"
              >
                {{ child.title }}
              </el-menu-item>
            </el-sub-menu>
            <el-menu-item v-else :index="item.path">
              <el-icon><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="left">
          <el-button text :icon="collapsed ? Expand : Fold" @click="collapsed = !collapsed" />
          <el-breadcrumb separator="/">
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="right">
          <el-button
            size="small"
            type="success"
            plain
            :icon="VideoPlay"
            @click="demoRef?.toggle()"
          >
            演示模式
          </el-button>
          <el-tag effect="plain" round type="success" size="small">
            {{ userStore.userInfo?.roles?.[0]?.name || '未授权' }}
          </el-tag>
          <el-dropdown trigger="click" @command="onCommand">
            <span class="user-trigger">
              <el-avatar :size="28">{{ avatarLabel }}</el-avatar>
              <span class="name">{{ userStore.userInfo?.real_name || '未登录' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item command="password">
                  <el-icon><Lock /></el-icon>修改密码
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowDown,
  Avatar,
  Bell,
  Cpu,
  DataAnalysis,
  DataLine,
  Document,
  Expand,
  Fold,
  Histogram,
  Lock,
  Monitor,
  Notebook,
  OfficeBuilding,
  PieChart,
  Setting,
  SwitchButton,
  User,
  VideoCamera,
  VideoPlay,
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

import { useUserStore } from '@/stores/user'
import DemoMode from '@/components/DemoMode.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const collapsed = ref(false)
const demoRef = ref<any>()

// 手机端自动折叠
function checkMobile() {
  collapsed.value = window.innerWidth < 768
}
checkMobile()
window.addEventListener('resize', checkMobile)

interface MenuItem {
  path: string
  title: string
  icon: any
  children?: MenuItem[]
  requiresAdmin?: boolean
}

const menu: MenuItem[] = [
  { path: '/dashboard', title: '数据大屏', icon: PieChart },
  { path: '/workbench', title: '工作台', icon: Monitor },
  {
    path: '/org',
    title: '组织架构',
    icon: OfficeBuilding,
    children: [
      { path: '/org/schools', title: '学校管理', icon: OfficeBuilding, requiresAdmin: true },
      { path: '/org/grades', title: '年级管理', icon: OfficeBuilding },
      { path: '/org/classes', title: '班级管理', icon: OfficeBuilding },
      { path: '/org/students', title: '学生管理', icon: Avatar },
      { path: '/org/teachers', title: '教师管理', icon: User, requiresAdmin: true },
      { path: '/org/subjects', title: '科目管理', icon: Notebook, requiresAdmin: true },
      { path: '/org/teaching', title: '任课关系', icon: Document, requiresAdmin: true },
      { path: '/org/faces', title: '人脸库管理', icon: Avatar },
    ],
  },
  {
    path: '/classroom',
    title: '课堂分析',
    icon: VideoCamera,
    children: [
      { path: '/classroom/cameras', title: '摄像头墙', icon: Monitor },
      { path: '/classroom/camera-manage', title: '摄像头管理', icon: Setting, requiresAdmin: true },
      { path: '/classroom/schedule', title: '课表管理', icon: Notebook },
    ],
  },
  { path: '/psychology', title: '心理健康', icon: Histogram },
  { path: '/correlation', title: '关联分析', icon: DataAnalysis },
  { path: '/alerts', title: '预警中心', icon: Bell },
  { path: '/reports', title: '报告中心', icon: Document },
  { path: '/ethics', title: '负责任 AI', icon: Lock },
  {
    path: '/enhance',
    title: 'AI 增强',
    icon: Cpu,
    children: [
      { path: '/enhance/cluster', title: '群体聚类', icon: PieChart },
      { path: '/enhance/intervention', title: '干预闭环', icon: DataLine },
      { path: '/enhance/graph', title: '知识图谱', icon: DataAnalysis },
      { path: '/enhance/multimodal', title: '多模态融合', icon: Histogram },
      { path: '/enhance/story', title: '小李的故事', icon: Avatar },
      { path: '/enhance/compare', title: '产品对比', icon: Document },
    ],
  },
  {
    path: '/system',
    title: '系统管理',
    icon: Setting,
    children: [
      { path: '/system/users', title: '用户管理', icon: User, requiresAdmin: true },
      { path: '/system/roles', title: '角色权限', icon: Lock, requiresAdmin: true },
      { path: '/system/ai', title: 'AI 服务监控', icon: Cpu },
    ],
  },
]

const visibleMenu = computed(() => {
  const filter = (items: MenuItem[]): MenuItem[] => {
    return items
      .filter((it) => !it.requiresAdmin || userStore.isAdmin)
      .map((it) =>
        it.children ? { ...it, children: filter(it.children) } : it,
      )
      .filter((it) => !it.children || it.children.length > 0)
  }
  return filter(menu)
})

const activeMenu = computed(() => route.path)

const breadcrumbs = computed(() => {
  const matched = route.matched.filter((m) => m.meta?.title)
  return matched.map((m) => ({ path: m.path, title: m.meta.title as string }))
})

const avatarLabel = computed(() => {
  const name = userStore.userInfo?.real_name || ''
  return name.slice(-1) || 'U'
})

async function onCommand(cmd: string) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确定退出登录吗？', '退出', { type: 'warning' }).catch(() => false)
    await userStore.logout()
    router.push('/login')
  } else if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'password') {
    router.push('/profile?tab=password')
  }
}
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
}

.aside {
  background: #0f172a;
  color: #fff;
  transition: width 0.2s;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  .brand {
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    padding: 0 18px;
    gap: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    &.collapsed {
      justify-content: center;
      padding: 0;
    }
    .logo-dot {
      width: 12px;
      height: 12px;
      flex-shrink: 0;
      background: linear-gradient(135deg, #22c55e, #0ea5e9);
      border-radius: 50%;
    }
    .brand-name {
      font-size: 16px;
      font-weight: 700;
      color: #f1f5f9;
      letter-spacing: 1px;
    }
  }

  .menu-scroll {
    flex: 1;
    :deep(.el-menu) {
      border-right: none;
    }
  }
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #fff;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.06);
  height: 56px;

  .left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .right {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .user-trigger {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    color: #1e293b;
    .name {
      font-size: 13px;
    }
  }
}

.main-content {
  background: #f1f5f9;
  padding: 16px;
}

@media (max-width: 768px) {
  .topbar :deep(.el-breadcrumb) {
    display: none;
  }
  .topbar .name {
    display: none;
  }
  .main-content {
    padding: 8px;
  }
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
