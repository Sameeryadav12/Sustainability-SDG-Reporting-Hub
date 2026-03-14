import { AuthProvider } from '@/features/auth/authStore'
import { AppRouter } from './router'

export function AppProviders() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  )
}
