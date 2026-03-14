/**
 * Form for creating a report section manually (admin only).
 */

import { useState, useEffect, type FormEvent } from 'react'
import type {
  ReportSectionScopeType,
  ReportSectionStatus,
  ReportSectionCreate,
} from './reportSectionsTypes'
import { SCOPE_TYPES, SECTION_STATUSES, SDG_IDS } from './reportSectionsTypes'
import type { Department } from '@/features/departments/departmentTypes'
import type { ApiError } from '@/api/client'
import styles from './ReportSectionsPage.module.css'

type ReportSectionFormProps = {
  reportingCycleId: string
  departments: Department[]
  onClose: () => void
  onSubmit: (data: ReportSectionCreate) => Promise<void>
}

export function ReportSectionForm({
  reportingCycleId,
  departments,
  onClose,
  onSubmit,
}: ReportSectionFormProps) {
  const [scopeType, setScopeType] = useState<ReportSectionScopeType>('SDG')
  const [scopeValue, setScopeValue] = useState('1')
  const [title, setTitle] = useState('')
  const [contentMarkdown, setContentMarkdown] = useState('')
  const [status, setStatus] = useState<ReportSectionStatus>('DRAFT')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (scopeType === 'SDG') setScopeValue('1')
    if (scopeType === 'DEPARTMENT' && departments.length > 0) setScopeValue(departments[0]?.id ?? '')
    if (scopeType === 'OVERALL') setScopeValue('summary')
    if (scopeType === 'THEME') setScopeValue('')
  }, [scopeType, departments])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    const t = title.trim()
    const c = contentMarkdown.trim()
    const sv = scopeValue.trim()
    if (!t || t.length < 3) {
      setError('Title must be at least 3 characters.')
      return
    }
    if (!c) {
      setError('Content (Markdown) is required.')
      return
    }
    if (!sv) {
      setError('Scope value is required.')
      return
    }
    setSaving(true)
    try {
      await onSubmit({
        reporting_cycle_id: reportingCycleId,
        scope_type: scopeType,
        scope_value: sv,
        title: t,
        content_markdown: c,
        status,
        generated_by: 'HUMAN',
      })
      onClose()
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to save report section.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={styles.backdrop} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <header className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>New report section</h2>
        </header>
        <form onSubmit={handleSubmit}>
        <div className={styles.modalBody}>
          {error && <p className={styles.formError} role="alert">{error}</p>}
          <div className={styles.fieldRow}>
            <div className={styles.field}>
              <label>Scope type</label>
              <select
                value={scopeType}
                onChange={(e) => setScopeType(e.target.value as ReportSectionScopeType)}
              >
                {SCOPE_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div className={styles.field}>
              <label>Scope value</label>
              {scopeType === 'SDG' && (
                <select value={scopeValue} onChange={(e) => setScopeValue(e.target.value)}>
                  {SDG_IDS.map((id) => (
                    <option key={id} value={id}>SDG {id}</option>
                  ))}
                </select>
              )}
              {scopeType === 'DEPARTMENT' && (
                <select value={scopeValue} onChange={(e) => setScopeValue(e.target.value)}>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              )}
              {scopeType === 'OVERALL' && (
                <input
                  type="text"
                  value="summary"
                  readOnly
                  disabled
                />
              )}
              {scopeType === 'THEME' && (
                <input
                  type="text"
                  value={scopeValue}
                  onChange={(e) => setScopeValue(e.target.value)}
                  placeholder="e.g. Climate"
                />
              )}
            </div>
          </div>
          <div className={styles.field}>
            <label>Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              minLength={3}
              placeholder="e.g. SDG 4 – Quality Education"
            />
          </div>
          <div className={styles.field}>
            <label>Content (Markdown)</label>
            <textarea
              value={contentMarkdown}
              onChange={(e) => setContentMarkdown(e.target.value)}
              required
              placeholder="## Overview\n..."
            />
          </div>
          <div className={styles.field}>
            <label>Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value as ReportSectionStatus)}>
              {SECTION_STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>
        <footer className={styles.modalFooter}>
          <button type="button" onClick={onClose} className={styles.secondaryBtn} disabled={saving}>
            Cancel
          </button>
          <button type="submit" className={styles.primaryBtn} disabled={saving}>
            {saving ? 'Saving…' : 'Create'}
          </button>
        </footer>
        </form>
      </div>
    </div>
  )
}
