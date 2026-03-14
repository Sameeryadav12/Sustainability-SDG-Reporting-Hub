/**
 * Metrics API for contributions.
 */

import { apiRequest } from '@/api/client'

export type Metric = {
  id: string
  contribution_id: string
  name: string
  value_number: number | null
  value_text: string | null
  unit: string | null
  year: number | null
  created_at: string
  updated_at: string
}

export type MetricCreate = {
  name: string
  value_number?: number | null
  value_text?: string | null
  unit?: string | null
  year?: number | null
}

export async function fetchMetrics(contributionId: string): Promise<Metric[]> {
  return apiRequest<Metric[]>(`/contributions/${contributionId}/metrics`)
}

export async function createMetric(contributionId: string, data: MetricCreate): Promise<Metric> {
  return apiRequest<Metric>(`/contributions/${contributionId}/metrics`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function deleteMetric(metricId: string): Promise<void> {
  await apiRequest<{ message: string }>(`/metrics/${metricId}`, { method: 'DELETE' })
}
