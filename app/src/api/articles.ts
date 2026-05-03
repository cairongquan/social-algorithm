import axios from 'axios'
import type { Article, ArticleCreate, ArticleUpdate, SquareArticle, ArticleComment } from '@/types/article'

const API_BASE = '/api/v1'

const getHeaders = () => {
  const token = localStorage.getItem('token')
  return { Authorization: `Bearer ${token}` }
}

export const articlesApi = {
  async list(): Promise<Article[]> {
    const response = await axios.get(`${API_BASE}/articles`)
    return response.data
  },

  async get(id: string): Promise<Article> {
    const response = await axios.get(`${API_BASE}/articles/${id}`)
    return response.data
  },

  async create(data: ArticleCreate): Promise<{ id: string }> {
    const response = await axios.post(`${API_BASE}/articles`, data, { headers: getHeaders() })
    return response.data
  },

  async update(id: string, data: ArticleUpdate): Promise<void> {
    await axios.put(`${API_BASE}/articles/${id}`, data, { headers: getHeaders() })
  },

  async delete(id: string): Promise<void> {
    await axios.delete(`${API_BASE}/articles/${id}`, { headers: getHeaders() })
  },

  async square(): Promise<SquareArticle[]> {
    const response = await axios.get(`${API_BASE}/articles/square`, { headers: getHeaders() })
    return response.data
  },

  async toggleLike(id: string): Promise<{ liked: boolean; likes_count: number }> {
    const response = await axios.post(`${API_BASE}/articles/${id}/like`, {}, { headers: getHeaders() })
    return response.data
  },

  async comments(id: string): Promise<ArticleComment[]> {
    const response = await axios.get(`${API_BASE}/articles/${id}/comments`)
    return response.data
  },

  async addComment(id: string, content: string): Promise<ArticleComment> {
    const response = await axios.post(
      `${API_BASE}/articles/${id}/comments`,
      { content },
      { headers: getHeaders() }
    )
    return response.data
  },

  async deleteComment(articleId: string, commentId: string): Promise<void> {
    await axios.delete(`${API_BASE}/articles/${articleId}/comments/${commentId}`, {
      headers: getHeaders()
    })
  },

  async markView(id: string): Promise<void> {
    await axios.post(`${API_BASE}/articles/${id}/view`, {}, { headers: getHeaders() })
  },

  async reportDwell(id: string, dwellSeconds: number): Promise<void> {
    await axios.post(
      `${API_BASE}/articles/${id}/dwell`,
      { dwell_seconds: dwellSeconds },
      { headers: getHeaders() }
    )
  }
}
