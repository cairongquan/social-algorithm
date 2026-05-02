import axios from 'axios'
import type { Tag, TagCreate, TagUpdate, TagPushPreview } from '@/types/tag'

const API_BASE = '/api/v1'

const getHeaders = () => {
  const token = localStorage.getItem('token')
  return { Authorization: `Bearer ${token}` }
}

export const tagsApi = {
  async list(): Promise<Tag[]> {
    const response = await axios.get(`${API_BASE}/tags`)
    return response.data
  },

  async create(data: TagCreate): Promise<{ id: string }> {
    const response = await axios.post(`${API_BASE}/tags`, data, { headers: getHeaders() })
    return response.data
  },

  async previewPushUsers(name: string): Promise<TagPushPreview> {
    const response = await axios.get(`${API_BASE}/tags/preview/push-users`, {
      params: { name },
      headers: getHeaders()
    })
    return response.data
  },

  async update(id: string, data: TagUpdate): Promise<void> {
    await axios.put(`${API_BASE}/tags/${id}`, data, { headers: getHeaders() })
  },

  async delete(id: string): Promise<void> {
    await axios.delete(`${API_BASE}/tags/${id}`, { headers: getHeaders() })
  }
}
