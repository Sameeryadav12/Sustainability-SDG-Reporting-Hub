/**
 * Reporting cycle create/edit form (modal).
 */

import { useState, FormEvent, useEffect } from 'react'
import type { ReportingCycle } from './reportingCycleTypes'
import { SDG_IDS } from './reportingCycleTypes'
import type { ApiError } from '@/api/client'
import styles from './ReportingCycleForm.module.css'

export type ReportingCycleFormValues = {
  name: string
  year: number
  start_date: string
  end_date: string
  description: string
  in_scope_sdgs: number[]
}

const currentYear = new Date().getFullYear()
const initialValues: ReportingCycleFormValues = {
  name: '',
  year: currentYear,
  start_date: '',
  end_date: '',
  description: '',
  in_scope_sdgs: [],
}

type ReportingCycleFormProps = {
  edit?: ReportingCycle | null
  onClose: () => void
  onSubmit: (values: ReportingCycleFormValues) => Promise<void>
}

function formatDate(s: string): string {
  if (!s) return ''
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  return d.toISOString().slice(0, 10)
}

export function ReportingCycleForm({ edit, onClose, onSubmit }: ReportingCycleFormProps) {
  const [values, setValues] = useState<ReportingCycleFormValues>(initialValues)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (edit) {
      setValues({
        name: edit.name,
        year: edit.year,
        start_date: formatDate(edit.start_date),
        end_date: formatDate(edit.end_date),
        description: edit.description ?? '',
        in_scope_sdgs: edit.in_scope_sdgs ?? [],
      })
    } else {
      setValues({
        ...initialValues,
        start_date: `${currentYear}-01-01`,
        end_date: `${currentYear}-12-31`,
      })
    }
    setError(null)
  }, [edit])

  const toggleSdg = (id: number) => {
    setValues((prev) => {
      const set = new Set(prev.in_scope_sdgs)
      if (set.has(id)) set.delete(id)
      else set.add(id)
      return { ...prev, in_scope_sdgs: [...set].sort((a, b) => a - b) }
    })
    setError(null)
  }

  const validate = (): string | null => {
    if (!values.name.trim()) return 'Name is required.'
    const y = values.year
    if (y < 2000 || y > 2100) return 'Year must be between 2000 and 2100.'
    if (!values.start_date || !values.end_date) return 'Start and end dates are required.'
    const start = new Date(values.start_date).getTime()
    const end = new Date(values.end_date).getTime()
    if (end < start) return 'End date must not be earlier than start date.'
    if (!values.in_scope_sdgs.length) return 'Select at least one SDG in scope.'
    return null
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    const err = validate()
    if (err) {
      setError(err)
      return
    }
    setSaving(true)
    try {
      await onSubmit({
        name: values.name.trim(),
        year: values.year,
        start_date: values.start_date,
        end_date: values.end_date,
        description: values.description.trim(),
        in_scope_sdgs: values.in_scope_sdgs,
      })
      onClose()
    } catch (e: unknown) {
      const apiErr = e as ApiError
      setError(apiErr?.message || apiErr?.detail || 'Unable to save reporting cycle.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={styles.overlay} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.title}>{edit ? 'Edit reporting cycle' : 'New reporting cycle'}</h2>
        <form onSubmit={handleSubmit} className={styles.form}>
          {error && <div className={styles.error} role="alert">{error}</div>}
          <div className={styles.field}>
            <label htmlFor="rc-name">Name</label>
            <input
              id="rc-name"
              type="text"
              value={values.name}
              onChange={(e) => setValues((p) => ({ ...p, name: e.target.value }))}
              disabled={saving}
              className={styles.input}
              required
            />
          </div>
          <div className={styles.row}>
            <div className={styles.field}>
              <label htmlFor="rc-year">Year</label>
              <input
                id="rc-year"
                type="number"
                min={2000}
                max={2100}
                value={values.year}
                onChange={(e) => setValues((p) => ({ ...p, year: Number(e.target.value) }))}
                disabled={saving}
                className={styles.input}
              />
            </div>
            <div className={styles.field}>
              <label htmlFor="rc-start">Start date</label>
              <input
                id="rc-start"
                type="date"
                value={values.start_date}
                onChange={(e) => setValues((p) => ({ ...p, start_date: e.target.value }))}
                disabled={saving}
                className={styles.input}
                required
              />
            </div>
            <div className={styles.field}>
              <label htmlFor="rc-end">End date</label>
              <input
                id="rc-end"
                type="date"
                value={values.end_date}
                onChange={(e) => setValues((p) => ({ ...p, end_date: e.target.value }))}
                disabled={saving}
                className={styles.input}
                required
              />
            </div>
          </div>
          <div className={styles.field}>
            <label htmlFor="rc-desc">Description (optional)</label>
            <textarea
              id="rc-desc"
              value={values.description}
              onChange={(e) => setValues((p) => ({ ...p, description: e.target.value }))}
              disabled={saving}
              className={styles.textarea}
              rows={2}
            />
          </div>
          <div className={styles.field}>
            <span className={styles.label}>In-scope SDGs (select at least one)</span>
            <div className={styles.sdgGrid}>
              {SDG_IDS.map((id) => (
                <label key={id} className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={values.in_scope_sdgs.includes(id)}
                    onChange={() => toggleSdg(id)}
                    disabled={saving}
                  />
                  <span>{id}</span>
                </label>
              ))}
            </div>
          </div>
          <div className={styles.actions}>
            <button type="button" onClick={onClose} className={styles.cancel} disabled={saving}>
              Cancel
            </button>
            <button type="submit" disabled={saving} className={styles.submit}>
              {saving ? 'Saving…' : edit ? 'Save changes' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
