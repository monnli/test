import { request } from './request'

export interface Scale {
  id: number
  code: string
  name: string
  target: string
  description: string | null
  question_count: number
  sort_order: number
}

export interface ScaleQuestion {
  id: number
  sort_order: number
  content: string
  options: { label: string; score: number }[]
  dimension: string | null
  reverse: boolean
}

export interface ScaleDetail {
  id: number
  code: string
  name: string
  target: string
  description: string | null
  interpretation: { min: number; max: number; level: string; color: string; advice: string }[]
  questions: ScaleQuestion[]
}

export interface AssessmentItem {
  id: number
  student_id: number
  student_name: string | null
  scale_id: number
  scale_code: string
  scale_name: string
  total_score: number
  level: string
  level_color: string
  advice: string | null
  dimension_scores: Record<string, number>
  completed_at: string | null
}

export interface TextAnalysisItem {
  id: number
  student_id: number
  title: string | null
  content: string
  polarity: string
  risk_level: string
  risk_keywords: string[]
  emotion_tags: string[]
  summary: string | null
  suggestion: string | null
  created_at: string
}

export interface ConversationItem {
  id: number
  student_id: number
  title: string
  risk_level: string
  message_count: number
  created_at: string
}

export interface MessageItem {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  risk_level: string | null
  risk_keywords: string[]
  created_at: string
}

export interface TimelinePoint {
  date: string
  score: number
  polarity: string
  risk_level: string
  source: string
  note: string | null
}

export interface PsychologyProfile {
  student: { id: number; name: string; class_id: number }
  latest_score: number
  top_risk: string
  assessments: AssessmentItem[]
  text_analyses: TextAnalysisItem[]
  conversations: ConversationItem[]
  timeline: TimelinePoint[]
}

export const listScales = () =>
  request<{ items: Scale[]; total: number }>({ url: '/psychology/scales', method: 'get' })

export const getScale = (id: number) =>
  request<ScaleDetail>({ url: `/psychology/scales/${id}`, method: 'get' })

export const seedScales = () =>
  request<{ seeded: number }>({ url: '/psychology/scales/seed', method: 'post' })

export const submitAssessment = (data: any) =>
  request<AssessmentItem>({ url: '/psychology/assessments', method: 'post', data })

export const listAssessments = (params?: any) =>
  request<{ items: AssessmentItem[]; total: number }>({
    url: '/psychology/assessments',
    method: 'get',
    params,
  })

export const analyzeText = (data: any) =>
  request<TextAnalysisItem>({ url: '/psychology/text-analyses', method: 'post', data })

export const listTextAnalyses = (studentId: number) =>
  request<{ items: TextAnalysisItem[]; total: number }>({
    url: '/psychology/text-analyses',
    method: 'get',
    params: { student_id: studentId },
  })

export const startConversation = (studentId: number, title?: string) =>
  request<ConversationItem>({
    url: '/psychology/conversations',
    method: 'post',
    data: { student_id: studentId, title },
  })

export const listConversations = (studentId?: number) =>
  request<{ items: ConversationItem[]; total: number }>({
    url: '/psychology/conversations',
    method: 'get',
    params: studentId ? { student_id: studentId } : {},
  })

export const getConversation = (id: number) =>
  request<ConversationItem & { messages: MessageItem[] }>({
    url: `/psychology/conversations/${id}`,
    method: 'get',
  })

export const postMessage = (convId: number, content: string) =>
  request<{ user_message: MessageItem; assistant_message: MessageItem; conversation: ConversationItem }>({
    url: `/psychology/conversations/${convId}/messages`,
    method: 'post',
    data: { content },
  })

export const getProfile = (studentId: number) =>
  request<PsychologyProfile>({
    url: `/psychology/students/${studentId}/profile`,
    method: 'get',
  })

export const getTimeline = (studentId: number, days = 60) =>
  request<{ items: TimelinePoint[] }>({
    url: `/psychology/students/${studentId}/timeline`,
    method: 'get',
    params: { days },
  })
