/**
 * Reporting cycles API.
 */

import { apiRequest } from '@/api/client'
import type {
  ReportingCycle,
  ReportingCycleCreate,
  ReportingCycleUpdate,
  CycleStatusActionResponse,
} from './reportingCycleTypes'

export async function fetchReportingCycles(status?: string): Promise<ReportingCycle[]> {
  const path = status ? `/reporting-cycles?status=${encodeURIComponent(status)}` : '/reporting-cycles'
  return apiRequest<ReportingCycle[]>(path)
}

export async function createReportingCycle(data: ReportingCycleCreate): Promise<ReportingCycle> {
  return apiRequest<ReportingCycle>('/reporting-cycles', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateReportingCycle(
  id: string,
  data: ReportingCycleUpdate
): Promise<ReportingCycle> {
  return apiRequest<ReportingCycle>(`/reporting-cycles/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function openReportingCycle(id: string): Promise<CycleStatusActionResponse> {
  return apiRequest<CycleStatusActionResponse>(`/reporting-cycles/${id}/open`, {
    method: 'POST',
  })
}

export async function closeReportingCycle(id: string): Promise<CycleStatusActionResponse> {
  return apiRequest<CycleStatusActionResponse>(`/reporting-cycles/${id}/close`, {
    method: 'POST',
  })
}
