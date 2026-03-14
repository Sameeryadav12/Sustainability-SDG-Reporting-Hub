import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import type { ApiError } from '@/api/client'
import type { Contribution } from './contributionTypes'
import {
  fetchContribution,
  updateContribution,
  submitContribution,
  approveContribution,
  rejectContribution,
} from './contributionApi'
import { ContributionStatusActions } from './ContributionStatusActions'
import { ContributionForm, type ContributionFormValues } from './ContributionForm'
import { MetricsForm } from './MetricsForm'
import { EvidenceUpload } from './EvidenceUpload'
import { CommentsSection } from './CommentsSection'
import { fetchReportingCycles } from '@/features/reportingCycles/reportingCycleApi'
import type { ReportingCycle } from '@/features/reportingCycles/reportingCycleTypes'
import { fetchDepartments } from '@/features/departments/departmentApi'
import type { Department } from '@/features/departments/departmentTypes'
import styles from './ContributionsPage.module.css'

const ROLE_ADMIN = 'ADMIN'
const ROLE_COORDINATOR = 'DEPARTMENT_COORDINATOR'

function formatDate(s: string | null | undefined): string {
  if (!s) return '—'
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function ContributionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [item, setItem] = useState<Contribution | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionFeedback, setActionFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [reportingCycles, setReportingCycles] = useState<ReportingCycle[]>([])
  const [departments, setDepartments] = useState<Department[]>([])

  const isAdmin = user?.role === ROLE_ADMIN
  const isCoordinator = user?.role === ROLE_COORDINATOR

  const canSubmit = !!user && (isAdmin || isCoordinator)
  const canApprove = !!user && isAdmin
  const canReject = !!user && isAdmin

  const load = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const data = await fetchContribution(id)
      setItem(data)
    } catch (e) {
      const err = e as ApiError
      console.error('Failed to load contribution details:', err)
      const message =
        err.status === 0
          ? 'Failed to load contribution details. Check that the backend is running and try again.'
          : err.detail && typeof err.detail === 'string'
            ? err.detail
            : err.message || 'Failed to load contribution details.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (editModalOpen) {
      Promise.all([fetchReportingCycles(), fetchDepartments()]).then(([cycles, depts]) => {
        setReportingCycles(cycles)
        setDepartments(depts)
      })
    }
  }, [editModalOpen])

  const handleSubmit = async () => {
    if (!item) return
    setActionFeedback(null)
    try {
      const updated = await submitContribution(item.id)
      setItem(updated)
      setActionFeedback({ type: 'success', message: 'Contribution submitted successfully.' })
      setTimeout(() => setActionFeedback(null), 4000)
    } catch (e) {
      const err = e as ApiError
      setActionFeedback({ type: 'error', message: err.message || 'Unable to submit contribution.' })
    }
  }

  const handleApprove = async (notes?: string) => {
    if (!item) return
    setActionFeedback(null)
    try {
      const updated = await approveContribution(item.id, notes ?? null)
      setItem(updated)
      setActionFeedback({ type: 'success', message: 'Contribution approved.' })
      setTimeout(() => setActionFeedback(null), 4000)
    } catch (e) {
      const err = e as ApiError
      setActionFeedback({ type: 'error', message: err.message || 'Unable to approve contribution.' })
    }
  }

  const handleReject = async (notes?: string) => {
    if (!item) return
    setActionFeedback(null)
    try {
      const updated = await rejectContribution(item.id, notes ?? null)
      setItem(updated)
      setActionFeedback({ type: 'success', message: 'Contribution rejected.' })
      setTimeout(() => setActionFeedback(null), 4000)
    } catch (e) {
      const err = e as ApiError
      setActionFeedback({ type: 'error', message: err.message || 'Unable to reject contribution.' })
    }
  }

  const canEdit =
    !!user &&
    item != null &&
    (isAdmin ||
      (isCoordinator &&
        item.status !== 'APPROVED' &&
        item.department_id != null &&
        user.department_id === item.department_id))

  const handleEditSubmit = async (values: ContributionFormValues) => {
    if (!item) return
    try {
      await updateContribution(item.id, {
        title: values.title,
        type: values.type,
        description: values.description,
        primary_sdg: values.primary_sdg,
        secondary_sdgs: values.secondary_sdgs,
        start_date: values.start_date,
        end_date: values.end_date,
        ...(isAdmin && values.department_id !== undefined ? { department_id: values.department_id } : {}),
      })
      setEditModalOpen(false)
      await load()
    } catch (e) {
      const err = e as ApiError
      throw err
    }
  }

  if (!id) {
    return (
      <div className={styles.page}>
        <p className={styles.error}>No contribution id provided.</p>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <button type="button" onClick={() => navigate(-1)} className={styles.backLink}>
            ← Back
          </button>
          <h1 className={styles.title}>Contribution details</h1>
        </div>
        {canEdit && item && (
          <button
            type="button"
            onClick={() => setEditModalOpen(true)}
            className={styles.primaryBtn}
          >
            Edit
          </button>
        )}
      </div>

      {loading && <p className={styles.loading}>Loading…</p>}
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
      {actionFeedback && (
        <p
          className={actionFeedback.type === 'success' ? styles.success : styles.error}
          role="alert"
        >
          {actionFeedback.message}
        </p>
      )}
      {!loading && !error && !item && <p className={styles.empty}>Contribution not found.</p>}

      {item && (
        <>
          <section className={styles.detailSection}>
            <h2 className={styles.detailTitle}>{item.title}</h2>
            <p className={styles.detailMeta}>
              <span className={styles.badge}>{item.status}</span>
              {item.type && <span className={styles.metaChip}>{item.type}</span>}
              {item.primary_sdg && <span className={styles.metaChip}>Primary SDG {item.primary_sdg}</span>}
            </p>
            <p className={styles.detailDescription}>{item.description || 'No description provided.'}</p>
          </section>

          <section className={styles.detailGrid}>
            <div className={styles.detailCard}>
              <h3>Context</h3>
              <dl>
                <div className={styles.detailRow}>
                  <dt>Reporting cycle</dt>
                  <dd>{item.reporting_cycle_name || '—'}</dd>
                </div>
                <div className={styles.detailRow}>
                  <dt>Department</dt>
                  <dd>{item.department_name || '—'}</dd>
                </div>
                <div className={styles.detailRow}>
                  <dt>Dates</dt>
                  <dd>
                    {formatDate(item.start_date)} – {formatDate(item.end_date)}
                  </dd>
                </div>
              </dl>
            </div>

            <div className={styles.detailCard}>
              <h3>SDGs</h3>
              <dl>
                <div className={styles.detailRow}>
                  <dt>Primary SDG</dt>
                  <dd>SDG {item.primary_sdg}</dd>
                </div>
                <div className={styles.detailRow}>
                  <dt>Secondary SDGs</dt>
                  <dd>
                    {item.secondary_sdgs?.length
                      ? item.secondary_sdgs.map((id) => `SDG ${id}`).join(', ')
                      : 'None'}
                  </dd>
                </div>
              </dl>
            </div>

            <div className={styles.detailCard}>
              <h3>Workflow</h3>
              <dl>
                <div className={styles.detailRow}>
                  <dt>Created</dt>
                  <dd>{formatDate(item.created_at)}</dd>
                </div>
                <div className={styles.detailRow}>
                  <dt>Last updated</dt>
                  <dd>{formatDate(item.updated_at)}</dd>
                </div>
                <div className={styles.detailRow}>
                  <dt>Approval notes</dt>
                  <dd>{item.approval_notes || '—'}</dd>
                </div>
              </dl>
            </div>
          </section>

          <section className={styles.detailSection}>
            <h2 className={styles.sectionHeading}>Actions</h2>
            <ContributionStatusActions
              contribution={item}
              canSubmit={canSubmit}
              canApprove={canApprove}
              canReject={canReject}
              onSubmit={handleSubmit}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          </section>

          <section className={styles.detailSection}>
            <h2 className={styles.sectionHeading}>Metrics</h2>
            <MetricsForm
              contributionId={item.id}
              canEdit={canEdit}
            />
          </section>
          <section className={styles.detailSection}>
            <h2 className={styles.sectionHeading}>Comments</h2>
            <CommentsSection
              contributionId={item.id}
              canAddComment={!!user && (isAdmin || isCoordinator)}
            />
          </section>
          <section className={styles.detailSection}>
            <h2 className={styles.sectionHeading}>Evidence</h2>
            <EvidenceUpload
              contributionId={item.id}
              canEdit={canEdit}
            />
          </section>
        </>
      )}

      {editModalOpen && item && (
        <ContributionForm
          initial={item}
          reportingCycles={reportingCycles}
          departments={departments}
          canEditDepartment={isAdmin}
          onSubmit={handleEditSubmit}
          onClose={() => setEditModalOpen(false)}
        />
      )}
    </div>
  )
}

