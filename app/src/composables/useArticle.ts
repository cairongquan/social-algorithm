import { ref } from 'vue'
import { articlesApi } from '@/api/articles'
import type { Article, ArticleCreate, ArticleUpdate } from '@/types/article'

export function useArticle() {
  const articles = ref<Article[]>([])
  const article = ref<Article | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchArticles() {
    loading.value = true
    error.value = null
    try {
      articles.value = await articlesApi.list()
    } catch (err) {
      error.value = '获取文章列表失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchArticle(id: string) {
    loading.value = true
    error.value = null
    try {
      article.value = await articlesApi.get(id)
    } catch (err) {
      error.value = '获取文章详情失败'
    } finally {
      loading.value = false
    }
  }

  async function createArticle(data: ArticleCreate) {
    loading.value = true
    error.value = null
    try {
      const result = await articlesApi.create(data)
      return result.id
    } catch (err) {
      error.value = '创建文章失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateArticle(id: string, data: ArticleUpdate) {
    loading.value = true
    error.value = null
    try {
      await articlesApi.update(id, data)
    } catch (err) {
      error.value = '更新文章失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteArticle(id: string) {
    loading.value = true
    error.value = null
    try {
      await articlesApi.delete(id)
    } catch (err) {
      error.value = '删除文章失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  return { articles, article, loading, error, fetchArticles, fetchArticle, createArticle, updateArticle, deleteArticle }
}
