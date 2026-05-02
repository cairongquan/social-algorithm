export type Tag = {
  id: string
  name: string
  created_at: string
  article_count?: number
  related_user_count?: number
}

export type TagCreate = {
  name: string
}

export type TagUpdate = {
  name: string
}

export type TagPushCandidate = {
  user_id: string
  username: string
  avatar_url?: string | null
  score: number
  push_discipline: string
  reason: string
}

export type TagPushPreview = {
  tag_name: string
  candidates: TagPushCandidate[]
}
