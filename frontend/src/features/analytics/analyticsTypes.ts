/**
 * Analytics summary types (aligned with backend summary response).
 *
 * The backend provides:
 * - overall counters
 * - breakdowns by status, SDG, department, and type
 */

export type AnalyticsStatusBucket = {
  status: string
  count: number
}

export type AnalyticsSdgBucket = {
  sdg: number
  count: number
}

export type AnalyticsDepartmentBucket = {
  department_id: string | null
  department_name: string | null
  count: number
}

export type AnalyticsTypeBucket = {
  type: string
  count: number
}

export type AnalyticsSummary = {
  reporting_cycle_id: string
  reporting_cycle_name: string | null
  total_contributions: number
  departments_with_contributions: number
  sdgs_covered: number
  metrics_count?: number | null
  status_breakdown: AnalyticsStatusBucket[]
  sdg_breakdown: AnalyticsSdgBucket[]
  department_breakdown: AnalyticsDepartmentBucket[]
  type_breakdown: AnalyticsTypeBucket[]
}

