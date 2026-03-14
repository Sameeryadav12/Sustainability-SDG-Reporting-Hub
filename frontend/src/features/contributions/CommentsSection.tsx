import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { ApiError } from '@/api/client'
import { fetchComments, createComment } from './commentsApi'
import type { Comment } from './commentsApi'
import styles from './ContributionsPage.module.css'

type CommentsSectionProps = {
  contributionId: string
  canAddComment: boolean
}

function formatCommentDate(s: string): string {
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  return d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })
}

export function CommentsSection({ contributionId, canAddComment }: CommentsSectionProps) {
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const list = await fetchComments(contributionId)
      setComments(list)
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to load comments.')
    } finally {
      setLoading(false)
    }
  }, [contributionId])

  useEffect(() => {
    load()
  }, [load])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!canAddComment) return
    const trimmed = text.trim()
    if (trimmed.length < 3) {
      setError('Comment must be at least 3 characters.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await createComment(contributionId, { text: trimmed })
      setText('')
      await load()
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Failed to add comment.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <p className={styles.loading}>Loading comments…</p>
  if (error && comments.length === 0)
    return <p className={styles.error}>{error}</p>

  return (
    <div>
      <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1rem' }}>
        {comments.map((c) => (
          <li
            key={c.id}
            style={{
              padding: '0.5rem 0',
              borderBottom: '1px solid #e5e7eb',
            }}
          >
            <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{c.text}</p>
            <small style={{ color: '#6b7280', fontSize: '0.8rem' }}>
              {formatCommentDate(c.created_at)}
            </small>
          </li>
        ))}
      </ul>
      {comments.length === 0 && !error && <p className={styles.empty}>No comments yet.</p>}
      {error && comments.length > 0 && (
        <p className={styles.error} style={{ marginBottom: '0.5rem' }}>{error}</p>
      )}
      {canAddComment && (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxWidth: 400 }}>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Add a comment…"
            rows={3}
            minLength={3}
            maxLength={2000}
            style={{ padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', resize: 'vertical' }}
          />
          <button type="submit" className={styles.primaryBtn} disabled={submitting || text.trim().length < 3}>
            {submitting ? 'Adding…' : 'Add comment'}
          </button>
        </form>
      )}
    </div>
  )
}
