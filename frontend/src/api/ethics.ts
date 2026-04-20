import { request } from './request'

export interface EthicsOverview {
  principles: { key: string; value: string; desc: string; icon: string }[]
  stats: {
    total_students: number
    total_face_records: number
    face_anonymized: number
    total_alerts: number
    red_alerts: number
    high_risk_blocked: number
    ai_messages_analyzed: number
    human_intervention_rate: number
    explainable_rate: number
  }
  risk_dictionary: { high: string[]; medium: string[]; low: string[] }
  system_prompt_excerpt: string
  audit_logs: { time: string; type: string; detail: string }[]
}

export const getEthicsOverview = () =>
  request<EthicsOverview>({ url: '/ethics/overview', method: 'get' })
