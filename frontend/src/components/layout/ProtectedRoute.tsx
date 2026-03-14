/**
 * Protects routes: redirects to /login if not authenticated.
 */

import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

type ProtectedRouteProps = {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isRestoring } = useAuth()
  const location = useLocation()

  if (isRestoring) {
    return (
      <div className="app-loading">
        <p>Loading…</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
