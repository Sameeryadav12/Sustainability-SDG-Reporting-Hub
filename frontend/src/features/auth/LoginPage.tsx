/**
 * Login page: email, password, validation, error display, loading state.
 */

import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { login as apiLogin } from '@/api/auth'
import { getBaseUrl, type ApiError } from '@/api/client'
import { useAuth } from '@/hooks/useAuth'
import styles from './LoginPage.module.css'

export function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connectionError, setConnectionError] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setConnectionError(false)
    const trimmedEmail = email.trim().toLowerCase()
    if (!trimmedEmail || !password) {
      setError('Email and password are required.')
      return
    }
    setLoading(true)
    try {
      const res = await apiLogin({ email: trimmedEmail, password })
      login(res.access_token, res.user)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      const apiErr = err as ApiError
      const isConnectionError = apiErr.status === 0
      const message =
        apiErr.status === 401
          ? 'Incorrect email or password.'
          : isConnectionError
            ? apiErr.message || `Cannot reach the server. Check your connection (API: ${getBaseUrl()})`
            : apiErr.message || 'Login failed. Please try again.'
      setError(message)
      setConnectionError(isConnectionError)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>Sustainability & SDG Reporting Hub</h1>
        <p className={styles.subtitle}>Sign in to continue</p>
        <form onSubmit={handleSubmit} className={styles.form}>
          {error && (
            <div className={styles.error} role="alert">
              {error}
              {connectionError && (
                <p style={{ margin: '0.5rem 0 0', fontSize: '0.9rem' }}>
                  Wait a moment, then click Sign in again — the server may be waking up.
                </p>
              )}
            </div>
          )}
          <div className={styles.field}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
              className={styles.input}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="password">Password</label>
            <div className={styles.passwordWrap}>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
                className={styles.input}
              />
              <button
                type="button"
                className={styles.togglePassword}
                onClick={() => setShowPassword((s) => !s)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>
          <button type="submit" disabled={loading} className={styles.submit}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
