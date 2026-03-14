/**
 * Auth API: login and current user.
 */

import { apiRequest } from './client'

export type UserSummary = {
  id: string
  name: string
  email: string
  role: string
  department_id: string | null
  is_active: boolean
}

export type TokenResponse = {
  access_token: string
  token_type: string
  expires_in: number
  user: UserSummary
}

export type LoginCredentials = {
  email: string
  password: string
}

export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  })
}

export async function getMe(): Promise<UserSummary> {
  return apiRequest<UserSummary>('/auth/me')
}
