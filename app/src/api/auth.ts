import axios from 'axios'
import type { LoginRequest, RegisterRequest, AuthResponse, User, UserProfileUpdate } from '@/types/user'

const API_BASE = '/api/v1'

export const authApi = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await axios.post(`${API_BASE}/auth/login`, data)
    return response.data
  },

  async register(data: RegisterRequest): Promise<void> {
    await axios.post(`${API_BASE}/auth/register`, data)
  },

  async me(token: string): Promise<User> {
    const response = await axios.get(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async updateProfile(token: string, data: UserProfileUpdate): Promise<{ access_token: string; user: User }> {
    const response = await axios.put(`${API_BASE}/auth/me`, data, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async uploadAvatar(token: string, file: File): Promise<{ avatar_url: string }> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await axios.post(`${API_BASE}/auth/avatar`, formData, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  }
}
