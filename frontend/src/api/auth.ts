import { request } from './request'
import type { UserInfo } from '@/stores/user'

export interface LoginResult {
  access_token: string
  refresh_token: string
  user: UserInfo
}

export function login(username: string, password: string): Promise<LoginResult> {
  return request<LoginResult>({
    url: '/auth/login',
    method: 'post',
    data: { username, password },
  })
}

export function me(): Promise<UserInfo> {
  return request<UserInfo>({ url: '/auth/me', method: 'get' })
}

export function logout(): Promise<void> {
  return request<void>({ url: '/auth/logout', method: 'post' })
}

export function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  return request<void>({
    url: '/auth/change-password',
    method: 'post',
    data: { old_password: oldPassword, new_password: newPassword },
  })
}
