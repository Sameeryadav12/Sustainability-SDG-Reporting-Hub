/**
 * Contribution types and shapes (aligned with backend).
 */

export type ContributionStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED'

export type ContributionType = 'RESEARCH' | 'TEACHING' | 'OPERATIONS' | 'POLICY' | 'COMMUNITY' | 'OTHER'

export const CONTRIBUTION_TYPES: ContributionType[] = [
  'RESEARCH',
  'TEACHING',
  'OPERATIONS',
  'POLICY',
  'COMMUNITY',
  'OTHER',
]

export type Contribution = {
  id: string
  title: string
  description: string
  type: ContributionType
  status: ContributionStatus
  primary_sdg: number
  secondary_sdgs: number[]
  start_date: string
  end_date: string
  reporting_cycle_id: string
  reporting_cycle_name?: string
  department_id: string | null
  department_name?: string | null
  approval_notes?: string | null
  created_at: string
  updated_at: string
}

export type ContributionCreate = {
  reporting_cycle_id: string
  title: string
  type: ContributionType
  description: string
  primary_sdg: number
  secondary_sdgs: number[]
  start_date: string
  end_date: string
  department_id?: string | null
}

export type ContributionUpdate = Partial<ContributionCreate>

export type ContributionFilters = {
  reporting_cycle_id?: string
  department_id?: string
  sdg?: number
  status?: ContributionStatus | ''
  type?: ContributionType | ''
}

export const SDG_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17] as const

