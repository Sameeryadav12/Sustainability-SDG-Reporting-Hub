/**
 * Evidence API for contributions.
 */

import { apiRequest, apiUploadFile } from '@/api/client'

export type EvidenceFile = {
  id: string
  contribution_id: string
  file_name: string
  file_url: string
  file_type: string
  uploaded_by_user_id: string
  uploaded_at: string
}

export async function fetchEvidence(contributionId: string): Promise<EvidenceFile[]> {
  return apiRequest<EvidenceFile[]>(`/contributions/${contributionId}/evidence`)
}

export async function uploadEvidence(contributionId: string, file: File): Promise<EvidenceFile> {
  const formData = new FormData()
  formData.append('file', file)
  return apiUploadFile<EvidenceFile>(`/contributions/${contributionId}/evidence/upload`, formData)
}

export async function deleteEvidence(evidenceId: string): Promise<void> {
  await apiRequest<{ message: string }>(`/evidence/${evidenceId}`, { method: 'DELETE' })
}
