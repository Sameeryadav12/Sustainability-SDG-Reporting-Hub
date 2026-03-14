import { useState } from 'react'
import type { Contribution } from './contributionTypes'
import styles from './ContributionStatusActions.module.css'

type ContributionStatusActionsProps = {
  contribution: Contribution
  canSubmit: boolean
  canApprove: boolean
  canReject: boolean
  onSubmit: () => Promise<void>
  onApprove: (notes?: string) => Promise<void>
  onReject: (notes?: string) => Promise<void>
}

export function ContributionStatusActions({
  contribution,
  canSubmit,
  canApprove,
  canReject,
  onSubmit,
  onApprove,
  onReject,
}: ContributionStatusActionsProps) {
  const [mode, setMode] = useState<'approve' | 'reject' | null>(null)
  const [notes, setNotes] = useState('')
  const [loadingAction, setLoadingAction] = useState<string | null>(null)
  const isDraftOrRejected = contribution.status === 'DRAFT' || contribution.status === 'REJECTED'

  const handleSubmit = async () => {
    setLoadingAction('submit')
    try {
      await onSubmit()
    } finally {
      setLoadingAction(null)
    }
  }

  const handleConfirm = async () => {
    if (mode === 'approve') {
      setLoadingAction('approve')
      try {
        await onApprove(notes || undefined)
        setMode(null)
        setNotes('')
      } finally {
        setLoadingAction(null)
      }
    } else if (mode === 'reject') {
      setLoadingAction('reject')
      try {
        await onReject(notes || undefined)
        setMode(null)
        setNotes('')
      } finally {
        setLoadingAction(null)
      }
    }
  }

  return (
    <div className={styles.actions}>
      {canSubmit && isDraftOrRejected && (
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!!loadingAction}
          className={styles.primaryBtn}
        >
          {loadingAction === 'submit' ? 'Submitting…' : 'Submit'}
        </button>
      )}

      {canApprove && contribution.status === 'SUBMITTED' && (
        <button
          type="button"
          onClick={() => setMode('approve')}
          className={styles.secondaryBtn}
          disabled={!!loadingAction}
        >
          Approve
        </button>
      )}

      {canReject && contribution.status === 'SUBMITTED' && (
        <button
          type="button"
          onClick={() => setMode('reject')}
          className={styles.dangerBtn}
          disabled={!!loadingAction}
        >
          Reject
        </button>
      )}

      {mode && (
        <div className={styles.inlineModal}>
          <div className={styles.inlineBox}>
            <p className={styles.inlineTitle}>{mode === 'approve' ? 'Approve contribution' : 'Reject contribution'}</p>
            <textarea
              className={styles.notes}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={mode === 'approve' ? 'Optional approval notes…' : 'Reason for rejection (optional)…'}
              rows={3}
            />
            <div className={styles.inlineFooter}>
              <button
                type="button"
                onClick={() => {
                  setMode(null)
                  setNotes('')
                }}
                className={styles.secondaryBtn}
                disabled={!!loadingAction}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                className={mode === 'approve' ? styles.primaryBtn : styles.dangerBtn}
                disabled={!!loadingAction}
              >
                {loadingAction ? (mode === 'approve' ? 'Approving…' : 'Rejecting…') : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

