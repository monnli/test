import { request } from './request'

export interface PipelineStatus {
  name: string
  status: 'not_loaded' | 'loading' | 'ready' | 'mock' | 'error'
  device: string
  error: string | null
  loaded_at: number | null
  requires_model: boolean
}

export interface FaceItem {
  id: number
  student_id: number
  student_name: string | null
  dim: number
  image_url: string | null
  image_hash: string | null
  confidence: number
  source: string
  created_at: string
}

export interface FaceStats {
  total_faces: number
  registered_students: number
  total_students: number
  coverage_percent: number
}

// ===== AI 监控 =====
export const getAiHealth = () => request<any>({ url: '/ai/health', method: 'get' })
export const getAiPipelines = () =>
  request<{ pipelines: PipelineStatus[] }>({ url: '/ai/pipelines', method: 'get' })
export const loadPipeline = (name: string) =>
  request<PipelineStatus>({ url: `/ai/pipelines/${name}/load`, method: 'post' })

// ===== AI 文本 =====
export interface SentimentResult {
  polarity: string
  emotion_tags: string[]
  risk_level: 'none' | 'low' | 'medium' | 'high'
  risk_keywords: string[]
  reason?: string
  pipeline_status?: string
  _mock?: boolean
}

export const aiSentiment = (text: string) =>
  request<SentimentResult>({ url: '/ai/text/sentiment', method: 'post', data: { text } })

export const aiSummarize = (text: string) =>
  request<any>({ url: '/ai/text/summarize', method: 'post', data: { text } })

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface ChatResult {
  reply: string
  risk_level: 'none' | 'low' | 'medium' | 'high'
  risk_keywords: string[]
  pipeline_status?: string
  _mock?: boolean
}

export const aiChat = (messages: ChatMessage[], system?: string) =>
  request<ChatResult>({
    url: '/ai/text/chat',
    method: 'post',
    data: { messages, system },
  })

export const aiEmotion = (imageBase64: string) =>
  request<any>({ url: '/ai/emotion', method: 'post', data: { image: imageBase64 } })

export const aiBehavior = (imageBase64: string, conf = 0.35) =>
  request<any>({
    url: '/ai/behavior',
    method: 'post',
    params: { conf },
    data: { image: imageBase64 },
  })

// ===== 人脸库 =====
export const getFaceStats = () => request<FaceStats>({ url: '/faces/stats', method: 'get' })

export const getFacesByStudent = (studentId: number) =>
  request<{ items: FaceItem[]; total: number }>({
    url: `/faces/by-student/${studentId}`,
    method: 'get',
  })

export const registerFace = (studentId: number, imageBase64: string) =>
  request<FaceItem & { duplicated?: boolean }>({
    url: `/faces/by-student/${studentId}`,
    method: 'post',
    data: { image: imageBase64 },
  })

export const deleteFace = (faceId: number) =>
  request<void>({ url: `/faces/${faceId}`, method: 'delete' })

export const deleteStudentFaces = (studentId: number) =>
  request<{ deleted: number }>({
    url: `/faces/by-student/${studentId}`,
    method: 'delete',
  })

export const recognizeFace = (imageBase64: string, threshold = 0.45) =>
  request<any>({
    url: '/faces/recognize',
    method: 'post',
    params: { threshold },
    data: { image: imageBase64 },
  })
