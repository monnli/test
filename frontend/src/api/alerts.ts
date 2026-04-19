import { request } from './request'

export interface AlertItem {
  id: number
  student_id: number
  student_name: string | null
  class_id: number | null
  level: 'green' | 'yellow' | 'orange' | 'red'
  score: number
  title: string
  reasons: string[]
  sources: string[]
  status: 'open' | 'acknowledged' | 'resolved' | 'closed'
  handler_id: number | null
  acknowledged_at: string | null
  resolved_at: string | null
  closed_at: string | null
  created_at: string
}

export interface AlertStats {
  total: number
  by_level: Record<string, number>
  by_status: Record<string, number>
}

export interface CorrelationItem {
  student_id: number
  name: string
  class_id: number
  psy_30d: number
  score_avg: number
  scale_score: number
  phone_count: number
  risk_score: number
  level: string
}

export const listAlerts = (params?: any) =>
  request<{ items: AlertItem[]; total: number }>({ url: '/alerts', method: 'get', params })

export const getAlertStats = () =>
  request<AlertStats>({ url: '/alerts/stats', method: 'get' })

export const recomputeAlerts = () =>
  request<{ processed: number; alerts_count: number; alerts: AlertItem[] }>({
    url: '/alerts/recompute',
    method: 'post',
  })

export const ackAlert = (id: number) =>
  request<AlertItem>({ url: `/alerts/${id}/acknowledge`, method: 'post' })

export const resolveAlert = (id: number, note?: string) =>
  request<AlertItem>({ url: `/alerts/${id}/resolve`, method: 'post', data: { note } })

export const closeAlert = (id: number) =>
  request<AlertItem>({ url: `/alerts/${id}/close`, method: 'post' })

export const listInterventions = (alertId: number) =>
  request<{ items: any[] }>({ url: `/alerts/${alertId}/interventions`, method: 'get' })

export const addIntervention = (alertId: number, data: any) =>
  request<any>({ url: `/alerts/${alertId}/interventions`, method: 'post', data })

export const getCorrelationMatrix = () =>
  request<{ items: CorrelationItem[]; fields: { key: string; label: string }[] }>({
    url: '/alerts/correlation/matrix',
    method: 'get',
  })
