export type Article = {
  id: string
  title: string
  content: string
  author: string
  created_at: string
  updated_at: string
  tags: Tag[]
}

export type SquareArticle = Article & {
  likes_count: number
  comments_count: number
  liked_by_me: boolean
}

export type ArticleComment = {
  id: string
  article_id: string
  user_id: string
  username: string
  content: string
  created_at: string
}

export type ArticleCreate = {
  title: string
  content: string
  tag_ids: string[]
}

export type ArticleUpdate = {
  title?: string
  content?: string
  tag_ids?: string[]
}

export type Tag = {
  id: string
  name: string
}
