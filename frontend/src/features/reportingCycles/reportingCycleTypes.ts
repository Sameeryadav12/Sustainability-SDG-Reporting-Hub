/**
 * Reporting cycle types (aligned with backend).
 */

export type ReportingCycleStatus = 'DRAFT' | 'OPEN' | 'CLOSED' | 'ARCHIVED'

export type ReportingCycle = {
  id: string
  name: string
  year: number
  start_date: string
  end_date: string
  status: ReportingCycleStatus
  description: string | null
  in_scope_sdgs: number[] | null
  created_at: string
  updated_at: string
}

export type ReportingCycleCreate = {
  name: string
  year: number
  start_date: string
  end_date: string
  description?: string | null
  in_scope_sdgs: number[]
}

export type ReportingCycleUpdate = {
  name?: string
  year?: number
  start_date?: string
  end_date?: string
  description?: string | null
  in_scope_sdgs?: number[]
}

export type CycleStatusActionResponse = {
  id: string
  status: ReportingCycleStatus
  message: string
}

export const SDG_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17] as const
