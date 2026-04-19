import { request } from './request'
import type { PageResult } from './orgs'

export interface UserItem {
  id: number
  username: string
  real_name: string
  phone: string | null
  email: string | null
  avatar: string | null
  school_id: number | null
  is_active: boolean
  last_login_at: string | null
  last_login_ip: string | null
  created_at: string
  roles: { code: string; name: string }[]
}

export interface RoleItem {
  id: number
  code: string
  name: string
  description: string | null
  is_builtin: boolean
  sort_order: number
}

export const listUsers = (params?: any) =>
  request<PageResult<UserItem>>({ url: '/users', method: 'get', params })

export const createUser = (data: any) => request<UserItem>({ url: '/users', method: 'post', data })

export const updateUser = (id: number, data: any) =>
  request<UserItem>({ url: `/users/${id}`, method: 'put', data })

export const deleteUser = (id: number) =>
  request<void>({ url: `/users/${id}`, method: 'delete' })

export const resetUserPassword = (id: number, newPassword: string) =>
  request<void>({
    url: `/users/${id}/reset-password`,
    method: 'post',
    data: { new_password: newPassword },
  })

export const listAllRoles = () =>
  request<{ items: RoleItem[] }>({ url: '/users/roles/all', method: 'get' })
