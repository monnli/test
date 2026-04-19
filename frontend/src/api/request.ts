import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const service: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000,
  withCredentials: false,
})

service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

service.interceptors.response.use(
  (response) => {
    const { code, message, data } = response.data || {}
    if (code === undefined) {
      return response.data
    }
    if (code === 0) {
      return data
    }
    ElMessage.error(message || '请求失败')
    return Promise.reject(new Error(message || 'Error'))
  },
  (error) => {
    const msg = error?.response?.data?.message || error?.message || '网络异常'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

export function request<T = unknown>(config: AxiosRequestConfig): Promise<T> {
  return service.request<unknown, T>(config)
}

export default service
