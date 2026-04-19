import { request } from './request'
import type { PageResult } from './orgs'

export interface VideoItem {
  id: number
  title: string
  class_id: number | null
  url: string | null
  storage_key: string
  size_bytes: number
  size_mb: number
  duration_seconds: number
  fps: number
  width: number
  height: number
  uploaded_by: number | null
  created_at: string
}

export interface AnalysisTaskItem {
  id: number
  video_id: number
  status: 'pending' | 'running' | 'success' | 'failed'
  progress: number
  processed_frames: number
  total_frames: number
  sample_interval_sec: number
  error_message: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
}

export interface TimelinePoint {
  time: number
  [key: string]: number
}

export interface TaskReport {
  task: AnalysisTaskItem
  video: VideoItem
  summary: any
  metrics: {
    total_person_detections: number
    hand_up_count: number
    phone_count: number
    engagement_score: number
  }
  behavior_timeline: TimelinePoint[]
  emotion_timeline: TimelinePoint[]
}

export const listVideos = (params?: any) =>
  request<PageResult<VideoItem>>({ url: '/classroom/videos', method: 'get', params })

export const uploadVideo = (formData: FormData) =>
  request<VideoItem>({
    url: '/classroom/videos',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const startAnalyze = (videoId: number, interval = 2.0) =>
  request<AnalysisTaskItem>({
    url: `/classroom/videos/${videoId}/analyze`,
    method: 'post',
    params: { interval },
  })

export const listVideoTasks = (videoId: number) =>
  request<{ items: AnalysisTaskItem[]; total: number }>({
    url: `/classroom/videos/${videoId}/tasks`,
    method: 'get',
  })

export const getTask = (taskId: number) =>
  request<AnalysisTaskItem>({ url: `/classroom/tasks/${taskId}`, method: 'get' })

export const getTaskReport = (taskId: number) =>
  request<TaskReport>({ url: `/classroom/tasks/${taskId}/report`, method: 'get' })
