/**
 * Comments API for contributions.
 */

import { apiRequest } from '@/api/client'

export type Comment = {
  id: string
  contribution_id: string
  author_user_id: string
  text: string
  created_at: string
}

export type CommentCreate = {
  text: string
}

export async function fetchComments(contributionId: string): Promise<Comment[]> {
  return apiRequest<Comment[]>(`/contributions/${contributionId}/comments`)
}

export async function createComment(
  contributionId: string,
  data: CommentCreate
): Promise<Comment> {
  return apiRequest<Comment>(`/contributions/${contributionId}/comments`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
