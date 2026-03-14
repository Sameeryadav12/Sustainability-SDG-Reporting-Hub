import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/features/auth/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { DepartmentsPage } from '@/pages/DepartmentsPage'
import { ReportingCyclesPage } from '@/pages/ReportingCyclesPage'
import { ContributionsPage } from '@/pages/ContributionsPage'
import { ContributionDetailPage } from '@/features/contributions/ContributionDetailPage'
import { AnalyticsPage } from '@/pages/AnalyticsPage'
import { ReportSectionsPage } from '@/pages/ReportSectionsPage'
import { ExportsPage } from '@/pages/ExportsPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="departments" element={<DepartmentsPage />} />
          <Route path="reporting-cycles" element={<ReportingCyclesPage />} />
          <Route path="contributions" element={<ContributionsPage />} />
          <Route path="contributions/:id" element={<ContributionDetailPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="report-sections" element={<ReportSectionsPage />} />
          <Route path="exports" element={<ExportsPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
