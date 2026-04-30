export type User = {
  user_id: string
  username: string
  avatar_url?: string | null
}

export type LoginRequest = {
  username: string
  password: string
}

export type RegisterRequest = {
  username: string
  password: string
}

export type AuthResponse = {
  access_token: string
  token_type: string
}

export type UserProfileUpdate = {
  username?: string
  password?: string
}
