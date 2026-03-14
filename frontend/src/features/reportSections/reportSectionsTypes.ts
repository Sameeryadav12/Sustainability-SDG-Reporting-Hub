/**
 * Report section types (aligned with backend schemas).
 */

export type ReportSectionScopeType = 'SDG' | 'DEPARTMENT' | 'THEME' | 'OVERALL'

export type ReportSectionStatus = 'DRAFT' | 'REVIEWED' | 'FINAL'

export type DraftGeneratedBy = 'AI' | 'HUMAN'

export const SCOPE_TYPES: ReportSectionScopeType[] = ['SDG', 'DEPARTMENT', 'OVERALL', 'THEME']

export const SECTION_STATUSES: ReportSectionStatus[] = ['DRAFT', 'REVIEWED', 'FINAL']

export const SDG_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17] as const

export type ReportSection = {
  id: string
  reporting_cycle_id: string
  scope_type: ReportSectionScopeType
  scope_value: string
  title: string
  content_markdown: string
  status: ReportSectionStatus
  generated_by: DraftGeneratedBy
  last_generated_at: string | null
  created_at: string
  updated_at: string
}

export type ReportSectionListItem = {
  id: string
  reporting_cycle_id: string
  scope_type: ReportSectionScopeType
  scope_value: string
  title: string
  status: ReportSectionStatus
  generated_by: DraftGeneratedBy
  updated_at: string
}

export type ReportSectionCreate = {
  reporting_cycle_id: string
  scope_type: ReportSectionScopeType
  scope_value: string
  title: string
  content_markdown: string
  status?: ReportSectionStatus
  generated_by?: DraftGeneratedBy
}

export type ReportSectionUpdate = {
  title?: string
  content_markdown?: string
  status?: ReportSectionStatus
  generated_by?: DraftGeneratedBy
}

export type ReportSectionGenerateRequest = {
  reporting_cycle_id: string
  scope_type: ReportSectionScopeType
  scope_value: string
  title?: string | null
  target_word_count?: number
  overwrite_existing?: boolean
}

export type ReportSectionGenerateResponse = ReportSection & {
  source_contribution_count?: number | null
}

export type CompiledReportResponse = {
  reporting_cycle_id: string
  cycle_name: string
  cycle_year: number
  section_count: number
  content_markdown: string
}
