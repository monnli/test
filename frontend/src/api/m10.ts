import { request } from './request'

export interface Camera {
  id: number
  school_id: number
  class_id: number | null
  class_name: string | null
  name: string
  location: string | null
  stream_url: string
  stream_type: string
  resolution: string | null
  status: string
  last_heartbeat: string | null
  note: string | null
  created_at: string
}

export interface Schedule {
  id: number
  class_id: number
  class_name: string | null
  subject_id: number
  subject_name: string | null
  teacher_id: number
  teacher_name: string | null
  weekday: number
  period: number
  start_time: string
  end_time: string
  effective_from: string
  effective_to: string
  note: string | null
}

export interface LiveSession {
  id: number
  title: string
  class_id: number
  teacher_id: number | null
  subject_id: number | null
  camera_id: number | null
  camera_name: string | null
  trigger_type: string
  started_at: string | null
  engagement_score: number
}

// 摄像头
export const listCameras = () =>
  request<{ items: Camera[]; total: number }>({ url: '/m10/cameras', method: 'get' })
export const createCamera = (data: any) =>
  request<Camera>({ url: '/m10/cameras', method: 'post', data })
export const updateCamera = (id: number, data: any) =>
  request<Camera>({ url: `/m10/cameras/${id}`, method: 'put', data })
export const deleteCamera = (id: number) =>
  request<void>({ url: `/m10/cameras/${id}`, method: 'delete' })

// 课表
export const listSchedules = (params?: any) =>
  request<{ items: Schedule[]; total: number }>({ url: '/m10/schedules', method: 'get', params })
export const createSchedule = (data: any) =>
  request<Schedule>({ url: '/m10/schedules', method: 'post', data })
export const updateSchedule = (id: number, data: any) =>
  request<Schedule>({ url: `/m10/schedules/${id}`, method: 'put', data })
export const deleteSchedule = (id: number) =>
  request<void>({ url: `/m10/schedules/${id}`, method: 'delete' })
export const checkScheduleConflict = (data: any) =>
  request<{ conflicts: string[]; has_conflict: boolean }>({
    url: '/m10/schedules/check-conflict',
    method: 'post',
    data,
  })
export const getActiveSchedules = () =>
  request<{ items: Schedule[]; total: number }>({
    url: '/m10/schedules/active',
    method: 'get',
  })

// 实时
export const manualStartLive = (cameraId: number) =>
  request<{ session_id: number }>({
    url: '/m10/live/session/manual-start',
    method: 'post',
    data: { camera_id: cameraId },
  })
export const manualStopLive = (sessionId: number) =>
  request<void>({
    url: `/m10/live/session/${sessionId}/stop`,
    method: 'post',
  })
export const listActiveSessions = () =>
  request<{ items: LiveSession[]; total: number }>({
    url: '/m10/live/session/active',
    method: 'get',
  })
export const getCameraStatus = (cameraId: number) =>
  request<{ camera_id: number; is_running: boolean; active_session_id: number | null }>({
    url: `/m10/live/camera/${cameraId}/status`,
    method: 'get',
  })
