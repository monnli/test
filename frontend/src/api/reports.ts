import { request } from './request'

export interface ReportItem {
  id: number
  type: 'class' | 'student' | 'school'
  target_id: number | null
  target_name: string | null
  title: string
  period: string | null
  summary: string | null
  pdf_key: string | null
  operator_id: number | null
  created_at: string
  content?: string
}

export const listReports = (params?: any) =>
  request<{ items: ReportItem[]; total: number }>({ url: '/reports', method: 'get', params })

export const getReport = (id: number) =>
  request<ReportItem>({ url: `/reports/${id}`, method: 'get' })

export const generateClassReport = (classId: number) =>
  request<ReportItem>({ url: `/reports/class/${classId}`, method: 'post' })

export const generateStudentReport = (studentId: number) =>
  request<ReportItem>({ url: `/reports/student/${studentId}`, method: 'post' })

export const generateSchoolReport = () =>
  request<ReportItem>({ url: '/reports/school', method: 'post' })

export function reportPdfUrl(reportId: number, token: string): string {
  const base = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
  return `${base}/reports/${reportId}/pdf?_t=${token}`
}
