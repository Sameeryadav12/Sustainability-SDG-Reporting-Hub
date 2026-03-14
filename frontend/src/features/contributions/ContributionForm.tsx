import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import type { Contribution, ContributionCreate } from './contributionTypes'
import { SDG_IDS, CONTRIBUTION_TYPES } from './contributionTypes'
import type { ReportingCycle } from '@/features/reportingCycles/reportingCycleTypes'
import type { Department } from '@/features/departments/departmentTypes'
import styles from './ContributionForm.module.css'

export type ContributionFormValues = {
  reporting_cycle_id: string
  title: string
  type: ContributionCreate['type']
  description: string
  primary_sdg: number
  secondary_sdgs: number[]
  start_date: string
  end_date: string
  department_id?: string | null
}

type ContributionFormProps = {
  initial?: Contribution | null
  reportingCycles: ReportingCycle[]
  departments: Department[]
  canEditDepartment: boolean
  onSubmit: (values: ContributionFormValues) => Promise<void>
  onClose: () => void
}

export function ContributionForm({
  initial,
  reportingCycles,
  departments,
  canEditDepartment,
  onSubmit,
  onClose,
}: ContributionFormProps) {
  const [values, setValues] = useState<ContributionFormValues>(() => {
    const base: ContributionFormValues = {
      reporting_cycle_id: initial?.reporting_cycle_id ?? '',
      title: initial?.title ?? '',
      type: initial?.type ?? 'OTHER',
      description: initial?.description ?? '',
      primary_sdg: initial?.primary_sdg ?? 1,
      secondary_sdgs: initial?.secondary_sdgs ?? [],
      start_date: initial?.start_date?.slice(0, 10) ?? '',
      end_date: initial?.end_date?.slice(0, 10) ?? '',
      department_id: initial?.department_id ?? undefined,
    }
    return base
  })

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!values.reporting_cycle_id && reportingCycles.length > 0) {
      setValues((v) => ({ ...v, reporting_cycle_id: reportingCycles[0]?.id ?? '' }))
    }
  }, [reportingCycles, values.reporting_cycle_id])

  useEffect(() => {
    if (canEditDepartment && departments.length > 0 && (values.department_id === undefined || values.department_id === '') && !initial) {
      setValues((v) => ({ ...v, department_id: departments[0]?.id ?? null }))
    }
  }, [canEditDepartment, departments, initial, values.department_id])

  const availableSecondarySdgs = useMemo(
    () => SDG_IDS.filter((id) => id !== values.primary_sdg),
    [values.primary_sdg]
  )

  const handleChange = (field: keyof ContributionFormValues, value: unknown) => {
    setValues((prev) => ({ ...prev, [field]: value }))
  }

  const toggleSecondarySdg = (id: number) => {
    setValues((prev) => {
      const exists = prev.secondary_sdgs.includes(id)
      const next = exists
        ? prev.secondary_sdgs.filter((x) => x !== id)
        : [...prev.secondary_sdgs, id]
      return { ...prev, secondary_sdgs: next }
    })
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    const start = values.start_date ? new Date(values.start_date) : null
    const end = values.end_date ? new Date(values.end_date) : null
    if (start && end && end < start) {
      setError('End date cannot be before start date.')
      return
    }

    const trimmed: ContributionFormValues = {
      ...values,
      title: values.title.trim(),
      description: values.description.trim(),
    }
    if (!trimmed.title) {
      setError('Title is required.')
      return
    }
    if (!trimmed.reporting_cycle_id) {
      setError('Reporting cycle is required.')
      return
    }
    if (canEditDepartment && !initial && (trimmed.department_id === undefined || trimmed.department_id === null || trimmed.department_id === '')) {
      setError('Please select a department.')
      return
    }

    setSubmitting(true)
    try {
      await onSubmit(trimmed)
      onClose()
    } catch (e) {
      let msg: string
      if (e && typeof e === 'object' && 'message' in e) {
        const m = (e as { message: unknown }).message
        msg = typeof m === 'string' ? m : (m != null ? String(m) : '')
      } else {
        msg = ''
      }
      if (msg === '[object Object]' || !msg.trim()) msg = 'Unable to save contribution.'
      else msg = msg.trim()
      setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.backdrop} role="dialog" aria-modal="true">
      <div className={styles.modal}>
        <header className={styles.header}>
          <h2 className={styles.title}>{initial ? 'Edit contribution' : 'New contribution'}</h2>
        </header>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.fieldRow}>
            <label className={styles.field}>
              <span>Reporting cycle</span>
              <select
                value={values.reporting_cycle_id}
                onChange={(e) => handleChange('reporting_cycle_id', e.target.value)}
                required
              >
                <option value="">Select cycle…</option>
                {reportingCycles.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name || c.year}
                  </option>
                ))}
              </select>
            </label>
            {canEditDepartment && (
              <label className={styles.field}>
                <span>Department</span>
                <select
                  value={values.department_id ?? ''}
                  onChange={(e) => handleChange('department_id', e.target.value || undefined)}
                  required={!initial}
                >
                  {!initial && <option value="">Select department…</option>}
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>

          <div className={styles.fieldRow}>
            <label className={styles.field}>
              <span>Title</span>
              <input
                type="text"
                value={values.title}
                onChange={(e) => handleChange('title', e.target.value)}
                required
              />
            </label>
          </div>

          <div className={styles.fieldRow}>
            <label className={styles.field}>
              <span>Type</span>
              <select
                value={values.type}
                onChange={(e) => handleChange('type', e.target.value as ContributionCreate['type'])}
                required
              >
                {CONTRIBUTION_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className={styles.fieldRow}>
            <label className={styles.field}>
              <span>Description</span>
              <textarea
                value={values.description}
                onChange={(e) => handleChange('description', e.target.value)}
                rows={4}
              />
            </label>
          </div>

          <div className={styles.fieldRow}>
            <label className={styles.field}>
              <span>Primary SDG</span>
              <select
                value={values.primary_sdg}
                onChange={(e) => {
                  const id = Number(e.target.value)
                  handleChange('primary_sdg', id)
                  setValues((prev) => ({
                    ...prev,
                    secondary_sdgs: prev.secondary_sdgs.filter((s) => s !== id),
                  }))
                }}
                required
              >
                {SDG_IDS.map((id) => (
                  <option key={id} value={id}>
                    SDG {id}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className={styles.fieldRow}>
            <fieldset className={styles.field}>
              <legend>Secondary SDGs</legend>
              <div className={styles.sdgGrid}>
                {availableSecondarySdgs.map((id) => (
                  <label key={id} className={styles.sdgOption}>
                    <input
                      type="checkbox"
                      checked={values.secondary_sdgs.includes(id)}
                      onChange={() => toggleSecondarySdg(id)}
                    />
                    <span>SDG {id}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          </div>

          <div className={styles.fieldRow}>
            <label className={styles.field}>
              <span>Start date</span>
              <input
                type="date"
                value={values.start_date}
                onChange={(e) => handleChange('start_date', e.target.value)}
              />
            </label>
            <label className={styles.field}>
              <span>End date</span>
              <input
                type="date"
                value={values.end_date}
                onChange={(e) => handleChange('end_date', e.target.value)}
              />
            </label>
          </div>

          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}

          <footer className={styles.footer}>
            <button type="button" onClick={onClose} className={styles.secondaryBtn} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className={styles.primaryBtn} disabled={submitting}>
              {submitting ? 'Saving…' : 'Save'}
            </button>
          </footer>
        </form>
      </div>
    </div>
  )
}

