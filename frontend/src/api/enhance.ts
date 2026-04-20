import { request } from './request'

export interface ClusterStat {
  cluster_id: number
  name: string
  color: string
  icon: string
  advice: string
  count: number
  avg_psy: number
  avg_score: number
  avg_scale: number
  avg_abnormal: number
  sample_students: string[]
}

export interface ClusterPoint {
  x: number
  y: number
  cluster: number
  name: string
  id: number
}

export interface ClusterResult {
  clusters: ClusterStat[]
  points: ClusterPoint[]
  axis_labels: { x: string; y: string }
  total: number
}

export interface ForecastResult {
  student: { id: number; name: string }
  history: { date: string; score: number }[]
  forecast: { date: string; score: number }[]
  avg_recent_7d: number
  avg_forecast_7d: number
  trend_diff: number
  trend_label: string
  trend_color: string
  risk_alert: boolean
  method: string
}

export interface InterventionOverview {
  total_alerts: number
  open_count: number
  resolved_count: number
  success_rate: number
  intervention_count: number
  avg_hours: number
  by_action: { name: string; value: number }[]
  funnel: { name: string; value: number }[]
}

export interface AlertJourney {
  alert: any
  student: { id: number; name: string } | null
  timeline_events: { time: string; type: string; label: string; color: string }[]
  interventions: any[]
  comparison: {
    before: { date: string; score: number }[]
    after: { date: string; score: number }[]
    avg_before: number
    avg_after: number
    improvement: number
  }
}

export interface GraphData {
  categories: { name: string; itemStyle: { color: string } }[]
  nodes: { id: string; name: string; category: number; value: number; symbolSize: number }[]
  links: { source: string; target: string; value: number }[]
}

export interface MultimodalData {
  student: { id: number; name: string }
  series: {
    psychology: { date: string; value: number }[]
    academic: { date: string; value: number }[]
    behavior: { date: string; value: number }[]
  }
  anomalies: { date: string; reason: string }[]
  summary: string
}

export interface DemoStep {
  path: string
  duration: number
  narrate: string
}

export const getCluster = (n = 5) =>
  request<ClusterResult>({ url: '/enhance/cluster', method: 'get', params: { n } })

export const getForecast = (studentId: number, horizon = 7) =>
  request<ForecastResult>({
    url: `/enhance/forecast/${studentId}`,
    method: 'get',
    params: { horizon },
  })

export const getInterventionOverview = () =>
  request<InterventionOverview>({ url: '/enhance/intervention/overview', method: 'get' })

export const getAlertJourney = (alertId: number) =>
  request<AlertJourney>({ url: `/enhance/intervention/journey/${alertId}`, method: 'get' })

export const getGraph = () =>
  request<GraphData>({ url: '/enhance/graph', method: 'get' })

export const getMultimodal = (studentId: number) =>
  request<MultimodalData>({ url: `/enhance/multimodal/${studentId}`, method: 'get' })

export const getDemoScript = () =>
  request<{ steps: DemoStep[] }>({ url: '/enhance/demo-script', method: 'get' })
