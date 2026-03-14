/**
 * Reporting cycles page: list, create (admin), edit/open/close (admin). Read-only for non-admins.
 */

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/hooks/useAuth'
import {
  fetchReportingCycles,
  createReportingCycle,
  updateReportingCycle,
  openReportingCycle,
  closeReportingCycle,
} from '@/features/reportingCycles/reportingCycleApi'
import type { ReportingCycle } from '@/features/reportingCycles/reportingCycleTypes'
import type { ReportingCycleFormValues } from '@/features/reportingCycles/ReportingCycleForm'
import { ReportingCycleForm } from '@/features/reportingCycles/ReportingCycleForm'
import type { ApiError } from '@/api/client'
import styles from './ReportingCyclesPage.module.css'

const ROLE_ADMIN = 'ADMIN'

function formatDate(s: string): string {
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function ReportingCyclesPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === ROLE_ADMIN

  const [list, setList] = useState<ReportingCycle[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState<'create' | 'edit' | null>(null)
  const [editing, setEditing] = useState<ReportingCycle | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchReportingCycles()
      setList(data)
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to load reporting cycles.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleCreate = async (values: ReportingCycleFormValues) => {
    await createReportingCycle(values)
    setModalOpen(null)
    setSuccess('Reporting cycle created successfully.')
    setTimeout(() => setSuccess(null), 4000)
    await load()
  }

  const handleUpdate = async (values: ReportingCycleFormValues) => {
    if (!editing) return
    await updateReportingCycle(editing.id, values)
    setEditing(null)
    setModalOpen(null)
    setSuccess('Reporting cycle updated successfully.')
    setTimeout(() => setSuccess(null), 4000)
    await load()
  }

  const handleOpen = async (cycle: ReportingCycle) => {
    if (!confirm(`Open "${cycle.name}"? Only one cycle can be open at a time.`)) return
    setActionLoading(cycle.id)
    setError(null)
    try {
      await openReportingCycle(cycle.id)
      setSuccess('Reporting cycle opened.')
      setTimeout(() => setSuccess(null), 4000)
      await load()
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Another reporting cycle is already open.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleClose = async (cycle: ReportingCycle) => {
    if (!confirm(`Close "${cycle.name}"?`)) return
    setActionLoading(cycle.id)
    setError(null)
    try {
      await closeReportingCycle(cycle.id)
      setSuccess('Reporting cycle closed.')
      setTimeout(() => setSuccess(null), 4000)
      await load()
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to close cycle.')
    } finally {
      setActionLoading(null)
    }
  }

  const openEdit = (cycle: ReportingCycle) => {
    setEditing(cycle)
    setModalOpen('edit')
  }

  const closeModal = () => {
    setModalOpen(null)
    setEditing(null)
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Reporting Cycles</h1>
        {isAdmin && (
          <button type="button" onClick={() => setModalOpen('create')} className={styles.primaryBtn}>
            New reporting cycle
          </button>
        )}
      </div>

      {loading && <p className={styles.status}>Loading…</p>}
      {success && <p className={styles.success} role="status">{success}</p>}
      {error && <p className={styles.error} role="alert">{error}</p>}
      {!loading && !error && list.length === 0 && (
        <p className={styles.empty}>No reporting cycles found.</p>
      )}
      {!loading && !error && list.length > 0 && (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Year</th>
                <th>Start</th>
                <th>End</th>
                <th>Status</th>
                <th>SDGs</th>
                {isAdmin && <th className={styles.actionsCol} />}
              </tr>
            </thead>
            <tbody>
              {list.map((cycle) => (
                <tr key={cycle.id}>
                  <td>{cycle.name}</td>
                  <td>{cycle.year}</td>
                  <td>{formatDate(cycle.start_date)}</td>
                  <td>{formatDate(cycle.end_date)}</td>
                  <td>
                    <span className={styles[`status_${cycle.status}`] ?? styles.status}>
                      {cycle.status}
                    </span>
                  </td>
                  <td>
                    {(cycle.in_scope_sdgs ?? []).length > 0
                      ? (cycle.in_scope_sdgs ?? []).join(', ')
                      : '—'}
                  </td>
                  {isAdmin && (
                    <td className={styles.actionsCol}>
                      <button
                        type="button"
                        onClick={() => openEdit(cycle)}
                        className={styles.linkBtn}
                      >
                        Edit
                      </button>
                      {cycle.status === 'DRAFT' && (
                        <button
                          type="button"
                          onClick={() => handleOpen(cycle)}
                          disabled={!!actionLoading}
                          className={styles.linkBtn}
                        >
                          {actionLoading === cycle.id ? 'Opening…' : 'Open'}
                        </button>
                      )}
                      {cycle.status === 'OPEN' && (
                        <button
                          type="button"
                          onClick={() => handleClose(cycle)}
                          disabled={!!actionLoading}
                          className={styles.linkBtn}
                        >
                          {actionLoading === cycle.id ? 'Closing…' : 'Close'}
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modalOpen === 'create' && (
        <ReportingCycleForm onClose={closeModal} onSubmit={handleCreate} />
      )}
      {modalOpen === 'edit' && editing && (
        <ReportingCycleForm edit={editing} onClose={closeModal} onSubmit={handleUpdate} />
      )}
    </div>
  )
}
