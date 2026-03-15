/**
 * Login page: email, password, validation, error display, loading state.
 * Polls health until server is reachable (handles Render free-tier cold start).
 */

import { useState, useEffect, useRef, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { login as apiLogin } from '@/api/auth'
import { checkHealth, getBaseUrl, type ApiError } from '@/api/client'
import { useAuth } from '@/hooks/useAuth'
import styles from './LoginPage.module.css'

const HEALTH_POLL_MS = 5000
const SERVER_READY_FALLBACK_MS = 90000 // show form after 90s even if health never succeeds

export function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connectionError, setConnectionError] = useState(false)
  const [loading, setLoading] = useState(false)
  const [serverReady, setServerReady] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    let cancelled = false
    const fallbackId = setTimeout(() => {
      if (!cancelled) setServerReady(true)
    }, SERVER_READY_FALLBACK_MS)
    const tryHealth = async (): Promise<boolean> => {
      const ok = await checkHealth()
      if (!cancelled && ok) {
        setServerReady(true)
        if (pollRef.current) {
          clearInterval(pollRef.current)
          pollRef.current = null
        }
      }
      return ok
    }
    tryHealth().then((ok) => {
      if (cancelled || ok) return
      pollRef.current = setInterval(tryHealth, HEALTH_POLL_MS)
    })
    return () => {
      cancelled = true
      clearTimeout(fallbackId)
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

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
        {!serverReady ? (
          <div className={styles.form} style={{ padding: '1rem 0', color: '#374151' }}>
            <p style={{ margin: 0, fontSize: '1rem' }}>Connecting to server…</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.875rem', color: '#6b7280' }}>
              Free-tier hosting may take up to a minute to wake up. Please wait.
            </p>
          </div>
        ) : (
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
        )}
      </div>
    </div>
  )
}
