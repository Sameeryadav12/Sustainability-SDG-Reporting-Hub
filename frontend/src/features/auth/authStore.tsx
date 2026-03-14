/**
 * Auth context and provider. Token in localStorage; restores session via /auth/me on load.
 */

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { getMe } from '@/api/auth'
import type { ApiError } from '@/api/client'
import type { User } from './authTypes'

const TOKEN_KEY = 'access_token'

type AuthContextValue = {
  user: User | null
  token: string | null
  isRestoring: boolean
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
  setUser: (user: User | null) => void
  setError: (message: string | null) => void
  authError: string | null
}

export const AuthContext = createContext<AuthContextValue | null>(null)

function loadToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

type AuthProviderProps = {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUserState] = useState<User | null>(null)
  const [token, setTokenState] = useState<string | null>(() => loadToken())
  const [isRestoring, setIsRestoring] = useState(!!loadToken())
  const [authError, setAuthError] = useState<string | null>(null)

  const setUser = useCallback((u: User | null) => {
    setUserState(u)
  }, [])

  const setError = useCallback((message: string | null) => {
    setAuthError(message)
  }, [])

  const login = useCallback((newToken: string, newUser: User) => {
    saveToken(newToken)
    setTokenState(newToken)
    setUserState(newUser)
    setAuthError(null)
    setIsRestoring(false)
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setTokenState(null)
    setUserState(null)
    setAuthError(null)
    setIsRestoring(false)
  }, [])

  useEffect(() => {
    const stored = loadToken()
    if (!stored) {
      setIsRestoring(false)
      return
    }
    getMe()
      .then((me) => {
        setUserState(me as User)
        setTokenState(stored)
      })
      .catch((err: ApiError) => {
        clearToken()
        setTokenState(null)
        setUserState(null)
        if (err.status === 401) {
          setAuthError('Your session has expired. Please log in again.')
        }
      })
      .finally(() => {
        setIsRestoring(false)
      })
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isRestoring,
      isAuthenticated: !!(token && user),
      login,
      logout,
      setUser,
      setError,
      authError,
    }),
    [user, token, isRestoring, login, logout, setUser, setError, authError]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
