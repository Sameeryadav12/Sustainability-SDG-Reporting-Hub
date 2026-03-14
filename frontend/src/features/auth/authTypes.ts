/**
 * Auth-related types (aligned with backend UserSummary).
 */

export type User = {
  id: string
  name: string
  email: string
  role: string
  department_id: string | null
  is_active: boolean
}

export type LoginCredentials = {
  email: string
  password: string
}

export type AuthState = {
  user: User | null
  token: string | null
  isRestoring: boolean
  isAuthenticated: boolean
}
