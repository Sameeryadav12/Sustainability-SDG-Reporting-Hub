/**
 * Exports API: CSV downloads and Markdown report.
 */

import { downloadFile } from '@/api/client'
import { apiRequest } from '@/api/client'
import type { CompiledReportResponse } from '@/features/reportSections/reportSectionsTypes'

export async function downloadContributionsCsv(reportingCycleId: string): Promise<void> {
  const params = new URLSearchParams({ reporting_cycle_id: reportingCycleId })
  await downloadFile(
    `/exports/contributions.csv?${params.toString()}`,
    `contributions_${reportingCycleId.slice(0, 8)}.csv`
  )
}

export async function downloadMetricsCsv(reportingCycleId: string): Promise<void> {
  const params = new URLSearchParams({ reporting_cycle_id: reportingCycleId })
  await downloadFile(
    `/exports/metrics.csv?${params.toString()}`,
    `metrics_${reportingCycleId.slice(0, 8)}.csv`
  )
}

export async function downloadEvidenceCsv(reportingCycleId: string): Promise<void> {
  const params = new URLSearchParams({ reporting_cycle_id: reportingCycleId })
  await downloadFile(
    `/exports/evidence.csv?${params.toString()}`,
    `evidence_${reportingCycleId.slice(0, 8)}.csv`
  )
}

export async function fetchMarkdownReport(
  reportingCycleId: string
): Promise<CompiledReportResponse> {
  const params = new URLSearchParams({ reporting_cycle_id: reportingCycleId })
  return apiRequest<CompiledReportResponse>(`/exports/report.md?${params.toString()}`)
}
