import { request } from './request'

export interface HealthData {
  service: string
  status: string
  timestamp: number
}

export function getHealth(): Promise<HealthData> {
  return request<HealthData>({ url: '/health', method: 'get' })
}

export function getDeepHealth(): Promise<any> {
  return request<any>({ url: '/health/deep', method: 'get' })
}
