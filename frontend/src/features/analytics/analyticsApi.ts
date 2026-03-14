/**
 * Analytics API client.
 */

import { apiRequest } from '@/api/client'
import type { AnalyticsSummary } from './analyticsTypes'

function ensureArray<T>(v: unknown): T[] {
  return Array.isArray(v) ? (v as T[]) : []
}

function ensureNumber(v: unknown, fallback: number): number {
  if (typeof v === 'number' && !Number.isNaN(v)) return v
  if (typeof v === 'string') {
    const n = Number(v)
    if (!Number.isNaN(n)) return n
  }
  return fallback
}

/** Normalize backend response so charts always get valid arrays. */
function normalizeSummary(raw: Record<string, unknown>): AnalyticsSummary {
  return {
    reporting_cycle_id: String(raw.reporting_cycle_id ?? ''),
    reporting_cycle_name: raw.reporting_cycle_name != null ? String(raw.reporting_cycle_name) : null,
    total_contributions: ensureNumber(raw.total_contributions, 0),
    departments_with_contributions: ensureNumber(raw.departments_with_contributions, 0),
    sdgs_covered: ensureNumber(raw.sdgs_covered, 0),
    metrics_count: raw.metrics_count != null ? ensureNumber(raw.metrics_count, 0) : null,
    status_breakdown: ensureArray(raw.status_breakdown).map((b: unknown) => ({
      status: String((b as Record<string, unknown>)?.status ?? ''),
      count: ensureNumber((b as Record<string, unknown>)?.count, 0),
    })),
    sdg_breakdown: ensureArray(raw.sdg_breakdown).map((b: unknown) => ({
      sdg: ensureNumber((b as Record<string, unknown>)?.sdg, 0),
      count: ensureNumber((b as Record<string, unknown>)?.count, 0),
    })),
    department_breakdown: ensureArray(raw.department_breakdown).map((b: unknown) => {
      const o = b as Record<string, unknown>
      return {
        department_id: o?.department_id != null ? String(o.department_id) : null,
        department_name: o?.department_name != null ? String(o.department_name) : null,
        count: ensureNumber(o?.count, 0),
      }
    }),
    type_breakdown: ensureArray(raw.type_breakdown).map((b: unknown) => {
      const o = b as Record<string, unknown>
      return {
        type: String(o?.type ?? ''),
        count: ensureNumber(o?.count, 0),
      }
    }),
  }
}

export async function fetchAnalyticsSummary(reportingCycleId: string): Promise<AnalyticsSummary> {
  const params = new URLSearchParams({ reporting_cycle_id: reportingCycleId })
  const raw = await apiRequest<Record<string, unknown>>(`/analytics/summary?${params.toString()}`)
  return normalizeSummary(raw)
}

