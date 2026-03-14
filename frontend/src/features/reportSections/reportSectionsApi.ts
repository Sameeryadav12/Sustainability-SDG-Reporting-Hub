/**
 * Report sections API client.
 */

import { apiRequest } from '@/api/client'
import type {
  ReportSection,
  ReportSectionCreate,
  ReportSectionUpdate,
  ReportSectionListItem,
  ReportSectionGenerateRequest,
  ReportSectionGenerateResponse,
  CompiledReportResponse,
} from './reportSectionsTypes'

export async function fetchReportSections(
  reportingCycleId: string,
  skip = 0,
  limit = 100
): Promise<ReportSectionListItem[]> {
  const params = new URLSearchParams({
    reporting_cycle_id: reportingCycleId,
    skip: String(skip),
    limit: String(limit),
  })
  return apiRequest<ReportSectionListItem[]>(`/report-sections?${params.toString()}`)
}

export async function fetchReportSection(id: string): Promise<ReportSection> {
  return apiRequest<ReportSection>(`/report-sections/${id}`)
}

export async function createReportSection(data: ReportSectionCreate): Promise<ReportSection> {
  return apiRequest<ReportSection>('/report-sections', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateReportSection(
  id: string,
  data: ReportSectionUpdate
): Promise<ReportSection> {
  return apiRequest<ReportSection>(`/report-sections/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function generateReportSection(
  data: ReportSectionGenerateRequest
): Promise<ReportSectionGenerateResponse> {
  return apiRequest<ReportSectionGenerateResponse>('/report-sections/generate', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function fetchMarkdownReport(reportingCycleId: string): Promise<CompiledReportResponse> {
  const params = new URLSearchParams({ reporting_cycle_id: reportingCycleId })
  return apiRequest<CompiledReportResponse>(`/exports/report.md?${params.toString()}`)
}
