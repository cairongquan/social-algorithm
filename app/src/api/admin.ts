import axios from 'axios'

const API_BASE = '/api/v1'

const getHeaders = () => {
  const token = localStorage.getItem('token')
  return { Authorization: `Bearer ${token}` }
}

export type AlgorithmSettings = {
  decay_factor: number
  similarity_weight: number
  hot_weight: number
  follow_weight: number
  liked_weight: number
  diversity_penalty: number
  hot_like_factor: number
  hot_comment_factor: number
  algo_mode: number
  dwell_threshold_seconds: number
}

export type AlgorithmCurrent = AlgorithmSettings & {
  mode_name: 'full_model' | 'hot_only' | 'similarity_only' | 'sim_hot'
}

export type ExperimentSummary = {
  mode: number
  mode_name: 'full_model' | 'hot_only' | 'similarity_only' | 'sim_hot'
  users: number
  recall_at_10: number
  ndcg_at_10: number
}

export type ExperimentReport = {
  generated_at: string
  summaries: ExperimentSummary[]
  csv_url: string
  md_url: string
  png_url: string
}

export const adminApi = {
  async getAlgorithmSettings(): Promise<AlgorithmSettings> {
    const response = await axios.get(`${API_BASE}/admin/algorithm-settings`, { headers: getHeaders() })
    return response.data
  },

  async getAlgorithmCurrent(): Promise<AlgorithmCurrent> {
    const response = await axios.get(`${API_BASE}/admin/algorithm-settings/current`, {
      headers: getHeaders()
    })
    return response.data
  },

  async updateAlgorithmSettings(payload: AlgorithmSettings): Promise<AlgorithmSettings> {
    const response = await axios.put(`${API_BASE}/admin/algorithm-settings`, payload, {
      headers: getHeaders()
    })
    return response.data
  },

  async resetAlgorithmSettings(): Promise<AlgorithmSettings> {
    const response = await axios.post(`${API_BASE}/admin/algorithm-settings/reset`, {}, {
      headers: getHeaders()
    })
    return response.data
  },

  async generateExperimentReport(): Promise<ExperimentReport> {
    const response = await axios.post(`${API_BASE}/admin/experiment-report`, {}, {
      headers: getHeaders()
    })
    return response.data
  },

  async fetchReportFile(fileUrl: string): Promise<Blob> {
    const response = await axios.get(fileUrl, {
      headers: getHeaders(),
      responseType: 'blob'
    })
    return response.data
  }
}
