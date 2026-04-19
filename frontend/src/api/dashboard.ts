import { request } from './request'

export interface DashboardAll {
  overview: {
    school_count: number
    grade_count: number
    class_count: number
    student_count: number
    teacher_count: number
    today_alerts: number
    open_alerts: number
    week_videos: number
    week_assessments: number
    psy_index: number
  }
  alert_distribution: { by_level: Record<string, number> }
  class_engagement: { class_id: number; class_name: string; student_count: number; engagement: number }[]
  emotion_30d: { date: string; score: number }[]
  behavior_today: { items: { name: string; value: number }[] }
  emotion_today: { items: { name: string; value: number }[] }
  recent_alerts: any[]
  top_risk: { student_id: number; student_name: string; level: string; score: number }[]
}

export const getDashboardAll = () =>
  request<DashboardAll>({ url: '/dashboard/all', method: 'get' })
