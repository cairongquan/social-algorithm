import axios from 'axios'

const API_BASE = '/api/v1'

const getHeaders = () => {
  const token = localStorage.getItem('token')
  return { Authorization: `Bearer ${token}` }
}

export type TopologyOverview = {
  users_count: number
  follows_count: number
  likes_count: number
  comments_count: number
  my_following: number
  my_followers: number
  my_attention_score: number
}

export type TopologyGraph = {
  nodes: Array<{ id: string; username: string; avatar_url?: string | null }>
  edges: Array<{ follower_id: string; followee_id: string }>
}

export const topologyApi = {
  async overview(): Promise<TopologyOverview> {
    const response = await axios.get(`${API_BASE}/topology/overview`, { headers: getHeaders() })
    return response.data
  },

  async graph(): Promise<TopologyGraph> {
    const response = await axios.get(`${API_BASE}/topology/graph`, { headers: getHeaders() })
    return response.data
  }
}
