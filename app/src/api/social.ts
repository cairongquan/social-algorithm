import axios from 'axios'

const API_BASE = '/api/v1'

const getHeaders = () => {
  const token = localStorage.getItem('token')
  return { Authorization: `Bearer ${token}` }
}

export type SocialUser = {
  id: string
  username: string
  avatar_url?: string | null
  followed_by_me: number
}

export const socialApi = {
  async users(): Promise<SocialUser[]> {
    const response = await axios.get(`${API_BASE}/social/users`, { headers: getHeaders() })
    return response.data
  },

  async toggleFollow(userId: string): Promise<{ followed: boolean }> {
    const response = await axios.post(`${API_BASE}/social/follow/${userId}`, {}, { headers: getHeaders() })
    return response.data
  }
}
