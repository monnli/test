import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import * as authApi from '@/api/auth'

export interface RoleInfo {
  code: string
  name: string
}

export interface DataScope {
  is_full: boolean
  school_ids: number[]
  grade_ids: number[] | null
  class_ids: number[] | null
  all_subjects_in_class_ids: number[]
  subject_filters: number[][]
}

export interface UserInfo {
  id: number
  username: string
  real_name: string
  phone: string | null
  email: string | null
  avatar: string | null
  school_id: number | null
  is_active: boolean
  is_super: boolean
  roles: RoleInfo[]
  last_login_at: string | null
  data_scope?: DataScope
}

export const useUserStore = defineStore('user', () => {
  const accessToken = ref<string>(localStorage.getItem('access_token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refresh_token') || '')
  const userInfo = ref<UserInfo | null>(null)

  const isLogin = computed(() => Boolean(accessToken.value))
  const roleCodes = computed(() => (userInfo.value?.roles || []).map((r) => r.code))
  const isAdmin = computed(
    () =>
      userInfo.value?.is_super ||
      roleCodes.value.includes('school_admin') ||
      roleCodes.value.includes('psy_teacher'),
  )

  function setTokens(access: string, refresh?: string) {
    accessToken.value = access
    localStorage.setItem('access_token', access)
    if (refresh) {
      refreshToken.value = refresh
      localStorage.setItem('refresh_token', refresh)
    }
  }

  async function login(username: string, password: string) {
    const data = await authApi.login(username, password)
    setTokens(data.access_token, data.refresh_token)
    userInfo.value = data.user
    return data
  }

  async function fetchMe() {
    if (!accessToken.value) return null
    const data = await authApi.me()
    userInfo.value = data
    return data
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch (_) {
      // 忽略
    }
    accessToken.value = ''
    refreshToken.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  function hasRole(...codes: string[]) {
    if (userInfo.value?.is_super) return true
    return codes.some((c) => roleCodes.value.includes(c))
  }

  return {
    accessToken,
    refreshToken,
    userInfo,
    isLogin,
    isAdmin,
    roleCodes,
    setTokens,
    login,
    logout,
    fetchMe,
    hasRole,
  }
})
