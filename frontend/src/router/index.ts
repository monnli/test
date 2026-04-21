import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const MainLayout = () => import('@/layouts/MainLayout.vue')

const placeholder = (title: string) => ({
  template: `<div class="placeholder-page"><h2>${title}</h2><p>该模块将于后续里程碑实现。</p></div>`,
})

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/workbench' },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/Index.vue'),
    meta: { title: '登录 · 青苗守护者', anonymous: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/Index.vue'),
    meta: { title: '数据大屏' },
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/workbench',
    children: [
      {
        path: 'workbench',
        name: 'Workbench',
        component: () => import('@/views/workbench/Index.vue'),
        meta: { title: '工作台' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Index.vue'),
        meta: { title: '个人中心' },
      },
      // 组织架构
      {
        path: 'org',
        meta: { title: '组织架构' },
        children: [
          {
            path: 'schools',
            component: () => import('@/views/org/Schools.vue'),
            meta: { title: '学校管理', requiresAdmin: true },
          },
          {
            path: 'grades',
            component: () => import('@/views/org/Grades.vue'),
            meta: { title: '年级管理' },
          },
          {
            path: 'classes',
            component: () => import('@/views/org/Classes.vue'),
            meta: { title: '班级管理' },
          },
          {
            path: 'students',
            component: () => import('@/views/org/Students.vue'),
            meta: { title: '学生管理' },
          },
          {
            path: 'teachers',
            component: () => import('@/views/org/Teachers.vue'),
            meta: { title: '教师管理', requiresAdmin: true },
          },
          {
            path: 'subjects',
            component: () => import('@/views/org/Subjects.vue'),
            meta: { title: '科目管理', requiresAdmin: true },
          },
          {
            path: 'teaching',
            component: () => import('@/views/org/Teaching.vue'),
            meta: { title: '任课关系', requiresAdmin: true },
          },
          {
            path: 'faces',
            component: () => import('@/views/org/FaceLibrary.vue'),
            meta: { title: '人脸库管理' },
          },
        ],
      },
      // 系统管理
      {
        path: 'system',
        meta: { title: '系统管理', requiresAdmin: true },
        children: [
          {
            path: 'users',
            component: () => import('@/views/system/Users.vue'),
            meta: { title: '用户管理', requiresAdmin: true },
          },
          {
            path: 'roles',
            component: () => import('@/views/system/Roles.vue'),
            meta: { title: '角色权限', requiresAdmin: true },
          },
          {
            path: 'ai',
            component: () => import('@/views/system/AiMonitor.vue'),
            meta: { title: 'AI 服务监控' },
          },
        ],
      },
      // 课堂分析
      {
        path: 'classroom',
        meta: { title: '课堂分析' },
        children: [
          { path: '', component: () => import('@/views/classroom/Videos.vue'), meta: { title: '视频库' } },
          { path: 'upload', component: () => import('@/views/classroom/Upload.vue'), meta: { title: '上传视频' } },
          { path: 'realtime', component: () => import('@/views/classroom/Realtime.vue'), meta: { title: '实时摄像头（笔记本）' } },
          { path: 'video/:videoId', component: () => import('@/views/classroom/VideoTasks.vue'), meta: { title: '视频任务' } },
          { path: 'task/:taskId', component: () => import('@/views/classroom/TaskDetail.vue'), meta: { title: '分析报告' } },
          // M10 新增
          { path: 'cameras', component: () => import('@/views/classroom/CameraWall.vue'), meta: { title: '摄像头墙' } },
          { path: 'camera-manage', component: () => import('@/views/classroom/CameraManage.vue'), meta: { title: '摄像头管理', requiresAdmin: true } },
          { path: 'live/:cameraId', component: () => import('@/views/classroom/CameraLive.vue'), meta: { title: '实时直播' } },
          { path: 'schedule', component: () => import('@/views/classroom/Schedule.vue'), meta: { title: '课表管理' } },
        ],
      },
      // 心理健康
      {
        path: 'psychology',
        meta: { title: '心理健康' },
        children: [
          { path: '', component: () => import('@/views/psychology/Index.vue'), meta: { title: '量表与档案' } },
          {
            path: 'student/:studentId',
            component: () => import('@/views/psychology/StudentProfile.vue'),
            meta: { title: '学生心理档案' },
          },
        ],
      },
      // 关联分析
      {
        path: 'correlation',
        component: () => import('@/views/correlation/Index.vue'),
        meta: { title: '关联分析' },
      },
      // 预警中心
      {
        path: 'alerts',
        component: () => import('@/views/alerts/Index.vue'),
        meta: { title: '预警中心' },
      },
      {
        path: 'reports',
        component: () => import('@/views/reports/Index.vue'),
        meta: { title: '报告中心' },
      },
      {
        path: 'ethics',
        component: () => import('@/views/ethics/Index.vue'),
        meta: { title: '负责任 AI' },
      },
      {
        path: 'enhance',
        meta: { title: 'AI 增强' },
        children: [
          { path: 'cluster', component: () => import('@/views/enhance/Cluster.vue'), meta: { title: '群体聚类' } },
          { path: 'intervention', component: () => import('@/views/enhance/Intervention.vue'), meta: { title: '干预闭环' } },
          { path: 'graph', component: () => import('@/views/enhance/Graph.vue'), meta: { title: '知识图谱' } },
          { path: 'multimodal', component: () => import('@/views/enhance/Multimodal.vue'), meta: { title: '多模态融合' } },
          { path: 'story', component: () => import('@/views/enhance/Story.vue'), meta: { title: '小李的故事' } },
          { path: 'compare', component: () => import('@/views/enhance/Compare.vue'), meta: { title: '产品对比' } },
        ],
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在', anonymous: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  if (to.meta?.title) {
    document.title = `${to.meta.title} · 青苗守护者`
  }

  if (to.meta?.anonymous) {
    next()
    return
  }

  const userStore = useUserStore()
  if (!userStore.accessToken) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  if (!userStore.userInfo) {
    try {
      await userStore.fetchMe()
    } catch (_) {
      await userStore.logout()
      next({ path: '/login' })
      return
    }
  }

  if (to.meta?.requiresAdmin && !userStore.isAdmin) {
    next({ path: '/workbench' })
    return
  }

  next()
})

export default router
