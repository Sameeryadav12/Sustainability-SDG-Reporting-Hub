import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import type { ApiError } from '@/api/client'
import type { Contribution } from '@/features/contributions/contributionTypes'
import {
  fetchContributions,
  createContribution,
  updateContribution,
  submitContribution,
} from '@/features/contributions/contributionApi'
import { ContributionFilters } from '@/features/contributions/ContributionFilters'
import type { ContributionFilters as Filters } from '@/features/contributions/contributionTypes'
import { ContributionForm, type ContributionFormValues } from '@/features/contributions/ContributionForm'
import { fetchReportingCycles } from '@/features/reportingCycles/reportingCycleApi'
import type { ReportingCycle } from '@/features/reportingCycles/reportingCycleTypes'
import { fetchDepartments } from '@/features/departments/departmentApi'
import type { Department } from '@/features/departments/departmentTypes'
import styles from '@/features/contributions/ContributionsPage.module.css'

const ROLE_ADMIN = 'ADMIN'
const ROLE_COORDINATOR = 'DEPARTMENT_COORDINATOR'

function formatDateShort(s: string | null | undefined): string {
  if (!s) return '—'
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function ContributionsPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const isAdmin = user?.role === ROLE_ADMIN
  const isCoordinator = user?.role === ROLE_COORDINATOR
  const isViewerOnly = !user || (!isAdmin && !isCoordinator)

  const [list, setList] = useState<Contribution[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<Filters>({})
  const [reportingCycles, setReportingCycles] = useState<ReportingCycle[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [modalMode, setModalMode] = useState<'create' | 'edit' | null>(null)
  const [editing, setEditing] = useState<Contribution | null>(null)
  const [savingListActionId, setSavingListActionId] = useState<string | null>(null)
  const [actionFeedback, setActionFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [cycles, depts, contributions] = await Promise.all([
        fetchReportingCycles(),
        fetchDepartments(),
        fetchContributions(filters),
      ])
      setReportingCycles(cycles)
      setDepartments(depts)
      setList(contributions)
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to load contributions.')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    load()
  }, [load])

  const canCreate = !!user && (isAdmin || isCoordinator)
  const canEdit = (c: Contribution): boolean => {
    if (!user) return false
    if (isAdmin) return true
    if (!isCoordinator) return false
    if (c.status === 'APPROVED') return false
    if (!c.department_id || user.department_id !== c.department_id) return false
    return true
  }

  const canSubmit = (c: Contribution): boolean => {
    if (!user) return false
    if (!(isAdmin || isCoordinator)) return false
    return c.status === 'DRAFT' || c.status === 'REJECTED'
  }

  const openCreate = () => {
    setEditing(null)
    setModalMode('create')
  }

  const openEdit = (c: Contribution) => {
    if (!canEdit(c)) return
    setEditing(c)
    setModalMode('edit')
  }

  const closeModal = () => {
    setModalMode(null)
    setEditing(null)
  }

  const handleFormSubmit = async (values: ContributionFormValues) => {
    try {
      if (modalMode === 'create') {
        await createContribution(values.reporting_cycle_id, {
          reporting_cycle_id: values.reporting_cycle_id,
          title: values.title,
          type: values.type,
          description: values.description,
          primary_sdg: values.primary_sdg,
          secondary_sdgs: values.secondary_sdgs,
          start_date: values.start_date,
          end_date: values.end_date,
          department_id: values.department_id ?? null,
        })
      } else if (editing) {
        await updateContribution(editing.id, {
          title: values.title,
          type: values.type,
          description: values.description,
          primary_sdg: values.primary_sdg,
          secondary_sdgs: values.secondary_sdgs,
          start_date: values.start_date,
          end_date: values.end_date,
          ...(isAdmin && values.department_id !== undefined ? { department_id: values.department_id } : {}),
        })
      }
      closeModal()
      await load()
    } catch (e) {
      const err = e as ApiError
      throw err
    }
  }

  const handleRowSubmit = async (c: Contribution) => {
    if (!canSubmit(c)) return
    setActionFeedback(null)
    setSavingListActionId(c.id)
    try {
      const updated = await submitContribution(c.id)
      setList((prev) =>
        prev.map((x) => (x.id === updated.id ? { ...x, status: updated.status, updated_at: updated.updated_at } : x))
      )
      setActionFeedback({ type: 'success', message: 'Contribution submitted successfully.' })
      setTimeout(() => setActionFeedback(null), 4000)
    } catch (e) {
      const err = e as ApiError
      setActionFeedback({ type: 'error', message: err.message || 'Unable to submit contribution.' })
    } finally {
      setSavingListActionId(null)
    }
  }

  const rows = useMemo(
    () =>
      list.map((c) => ({
        ...c,
        reportingCycleLabel: c.reporting_cycle_name ?? '',
        departmentLabel: c.department_name ?? '',
      })),
    [list]
  )

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Contributions</h1>
        {canCreate && (
          <button type="button" onClick={openCreate} className={styles.primaryBtn}>
            New contribution
          </button>
        )}
      </div>

      <ContributionFilters
        value={filters}
        onChange={setFilters}
        reportingCycles={reportingCycles}
        departments={departments}
      />

      {loading && <p className={styles.loading}>Loading…</p>}
      {actionFeedback && (
        <p
          className={actionFeedback.type === 'success' ? styles.success : styles.error}
          role="alert"
        >
          {actionFeedback.message}
        </p>
      )}
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
      {!loading && !error && rows.length === 0 && (
        <p className={styles.empty}>No contributions found.</p>
      )}

      {!loading && !error && rows.length > 0 && (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Title</th>
                <th>Department</th>
                <th>Reporting cycle</th>
                <th>Primary SDG</th>
                <th>Type</th>
                <th className={styles.statusCol}>Status</th>
                <th className={styles.actionsCol} />
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => {
                const canEditRow = canEdit(c)
                const canSubmitRow = canSubmit(c)
                return (
                  <tr key={c.id}>
                    <td>
                      <button
                        type="button"
                        className={styles.linkBtn}
                        onClick={() => navigate(`/contributions/${c.id}`)}
                      >
                        {c.title}
                      </button>
                    </td>
                    <td>{c.departmentLabel || '—'}</td>
                    <td>{c.reportingCycleLabel || '—'}</td>
                    <td>SDG {c.primary_sdg}</td>
                    <td>{c.type}</td>
                    <td className={styles.statusCol}>
                      <span className={styles[`status_${c.status}`] ?? styles.status}>
                        {c.status}
                      </span>
                      <small>{formatDateShort(c.updated_at)}</small>
                    </td>
                    <td className={styles.actionsCol}>
                      <div className={styles.rowActions}>
                        {canEditRow && (
                          <button
                            type="button"
                            onClick={() => openEdit(c)}
                            className={styles.linkBtn}
                          >
                            Edit
                          </button>
                        )}
                        {canSubmitRow && (
                          <button
                            type="button"
                            disabled={savingListActionId === c.id}
                            onClick={() => handleRowSubmit(c)}
                            className={styles.linkBtn}
                          >
                            {savingListActionId === c.id ? 'Submitting…' : 'Submit'}
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => navigate(`/contributions/${c.id}`)}
                          className={styles.linkBtn}
                        >
                          View
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {modalMode && !isViewerOnly && (
        <ContributionForm
          initial={modalMode === 'edit' ? editing : null}
          reportingCycles={reportingCycles}
          departments={departments}
          canEditDepartment={isAdmin}
          onSubmit={handleFormSubmit}
          onClose={closeModal}
        />
      )}
    </div>
  )
}
