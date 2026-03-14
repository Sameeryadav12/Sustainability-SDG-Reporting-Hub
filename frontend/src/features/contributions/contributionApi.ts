/**
 * Contributions API.
 */

import { apiRequest } from '@/api/client'
import type {
  Contribution,
  ContributionCreate,
  ContributionUpdate,
  ContributionFilters,
} from './contributionTypes'

/** Backend may return primary_sdg_id / secondary_sdg_ids; normalize to frontend shape. Never throws. */
function normalizeContribution(raw: Record<string, unknown>): Contribution {
  try {
    const id = String(raw?.id ?? '')
    const start = raw?.start_date != null ? String(raw.start_date).slice(0, 10) : ''
    const end = raw?.end_date != null ? String(raw.end_date).slice(0, 10) : ''
    let primarySdg = 1
    if (typeof raw?.primary_sdg === 'number' && !Number.isNaN(raw.primary_sdg)) primarySdg = raw.primary_sdg
    else if (raw?.primary_sdg_id != null) {
      const n = Number(raw.primary_sdg_id)
      if (!Number.isNaN(n)) primarySdg = n
    }
    let secondarySdgs: number[] = []
    if (Array.isArray(raw?.secondary_sdg_ids)) {
      secondarySdgs = (raw.secondary_sdg_ids as unknown[]).map((x) => Number(x)).filter((n) => !Number.isNaN(n) && n >= 1 && n <= 17)
    } else if (Array.isArray(raw?.secondary_sdgs)) {
      secondarySdgs = (raw.secondary_sdgs as unknown[]).map((x) => Number(x)).filter((n) => !Number.isNaN(n))
    }
    return {
      id,
      title: String(raw?.title ?? ''),
      description: String(raw?.description ?? ''),
      type: (raw?.type as Contribution['type']) ?? 'OTHER',
      status: (raw?.status as Contribution['status']) ?? 'DRAFT',
      primary_sdg: primarySdg,
      secondary_sdgs: secondarySdgs,
      start_date: start,
      end_date: end,
      reporting_cycle_id: String(raw?.reporting_cycle_id ?? ''),
      reporting_cycle_name: raw?.reporting_cycle_name != null ? String(raw.reporting_cycle_name) : undefined,
      department_id: raw?.department_id != null && raw.department_id !== '' ? String(raw.department_id) : null,
      department_name: raw?.department_name != null ? String(raw.department_name) : undefined,
      approval_notes: raw?.approval_notes != null ? String(raw.approval_notes) : undefined,
      created_at: String(raw?.created_at ?? ''),
      updated_at: String(raw?.updated_at ?? ''),
    }
  } catch {
    return {
      id: String(raw?.id ?? ''),
      title: '—',
      description: '',
      type: 'OTHER',
      status: 'DRAFT',
      primary_sdg: 1,
      secondary_sdgs: [],
      start_date: '',
      end_date: '',
      reporting_cycle_id: String(raw?.reporting_cycle_id ?? ''),
      department_id: null,
      created_at: '',
      updated_at: '',
    }
  }
}

export async function fetchContributions(filters: ContributionFilters = {}): Promise<Contribution[]> {
  const params = new URLSearchParams()
  if (filters.reporting_cycle_id) params.set('reporting_cycle_id', filters.reporting_cycle_id)
  if (filters.department_id) params.set('department_id', filters.department_id)
  if (typeof filters.sdg === 'number') params.set('sdg', String(filters.sdg))
  if (filters.status) params.set('status', filters.status)
  if (filters.type) params.set('type', filters.type)

  const query = params.toString()
  const path = query ? `/contributions?${query}` : '/contributions'
  const list = await apiRequest<Record<string, unknown>[]>(path)
  return list.map((row) => normalizeContribution(row))
}

export async function fetchContribution(id: string): Promise<Contribution> {
  const raw = await apiRequest<Record<string, unknown>>(`/contributions/${id}`)
  return normalizeContribution(raw)
}

/** Build backend create payload (primary_sdg_id, secondary_sdg_ids). */
function toBackendCreate(data: ContributionCreate): Record<string, unknown> {
  const { primary_sdg, secondary_sdgs, ...rest } = data
  return {
    ...rest,
    primary_sdg_id: primary_sdg,
    secondary_sdg_ids: secondary_sdgs?.length ? secondary_sdgs : null,
  }
}

/** Build backend update payload; only include defined fields. */
function toBackendUpdate(data: ContributionUpdate): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  if (data.title !== undefined) out.title = data.title
  if (data.type !== undefined) out.type = data.type
  if (data.description !== undefined) out.description = data.description
  if (data.primary_sdg !== undefined) out.primary_sdg_id = data.primary_sdg
  if (data.secondary_sdgs !== undefined) out.secondary_sdg_ids = data.secondary_sdgs?.length ? data.secondary_sdgs : null
  if (data.start_date !== undefined) out.start_date = data.start_date || null
  if (data.end_date !== undefined) out.end_date = data.end_date || null
  if (data.department_id !== undefined) out.department_id = data.department_id ?? null
  return out
}

export async function createContribution(
  reportingCycleId: string,
  data: ContributionCreate
): Promise<Contribution> {
  const raw = await apiRequest<Record<string, unknown>>(
    `/reporting-cycles/${reportingCycleId}/contributions`,
    { method: 'POST', body: JSON.stringify(toBackendCreate(data)) }
  )
  return normalizeContribution(raw)
}

export async function updateContribution(id: string, data: ContributionUpdate): Promise<Contribution> {
  const raw = await apiRequest<Record<string, unknown>>(`/contributions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(toBackendUpdate(data)),
  })
  return normalizeContribution(raw)
}

export async function submitContribution(id: string): Promise<Contribution> {
  const raw = await apiRequest<Record<string, unknown>>(`/contributions/${id}/submit`, {
    method: 'POST',
  })
  return normalizeContribution(raw)
}

export async function approveContribution(
  id: string,
  notes?: string | null
): Promise<Contribution> {
  const raw = await apiRequest<Record<string, unknown>>(`/contributions/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify({ notes: notes ?? null }),
  })
  return normalizeContribution(raw)
}

export async function rejectContribution(
  id: string,
  notes?: string | null
): Promise<Contribution> {
  const raw = await apiRequest<Record<string, unknown>>(`/contributions/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ notes: notes ?? null }),
  })
  return normalizeContribution(raw)
}

