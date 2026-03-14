/**
 * Department create/edit form (modal). Used by DepartmentsPage.
 */

import { useState, FormEvent, useEffect } from 'react'
import type { Department, DepartmentType } from './departmentTypes'
import { DEPARTMENT_TYPES } from './departmentTypes'
import type { ApiError } from '@/api/client'
import styles from './DepartmentForm.module.css'

export type DepartmentFormValues = {
  name: string
  code: string
  type: DepartmentType
}

const initialValues: DepartmentFormValues = {
  name: '',
  code: '',
  type: 'ACADEMIC',
}

type DepartmentFormProps = {
  edit?: Department | null
  onClose: () => void
  onSubmit: (values: DepartmentFormValues) => Promise<void>
}

export function DepartmentForm({ edit, onClose, onSubmit }: DepartmentFormProps) {
  const [values, setValues] = useState<DepartmentFormValues>(initialValues)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (edit) {
      setValues({
        name: edit.name,
        code: edit.code,
        type: edit.type,
      })
    } else {
      setValues(initialValues)
    }
    setError(null)
  }, [edit])

  const handleChange = (field: keyof DepartmentFormValues, value: string | DepartmentType) => {
    setError(null)
    if (field === 'code' && typeof value === 'string') {
      setValues((prev) => ({ ...prev, code: value.trim().toUpperCase() }))
      return
    }
    setValues((prev) => ({ ...prev, [field]: value }))
  }

  const validate = (): string | null => {
    const name = values.name.trim()
    const code = values.code.trim().toUpperCase()
    if (!name || name.length < 2) return 'Name must be at least 2 characters.'
    if (!code || code.length < 2) return 'Code must be at least 2 characters.'
    if (code.length > 20) return 'Code must be at most 20 characters.'
    if (!/^[A-Za-z0-9_\-]+$/.test(code)) {
      return 'Code may only contain letters, numbers, underscores, and hyphens.'
    }
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
        code: values.code.trim().toUpperCase(),
        type: values.type,
      })
      onClose()
    } catch (e: unknown) {
      const apiErr = e as ApiError
      setError(apiErr?.message || apiErr?.detail || 'Unable to save department.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={styles.overlay} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.title}>{edit ? 'Edit department' : 'New department'}</h2>
        <form onSubmit={handleSubmit} className={styles.form}>
          {error && <div className={styles.error} role="alert">{error}</div>}
          <div className={styles.field}>
            <label htmlFor="dept-name">Name</label>
            <input
              id="dept-name"
              type="text"
              value={values.name}
              onChange={(e) => handleChange('name', e.target.value)}
              disabled={saving}
              className={styles.input}
              required
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="dept-code">Code</label>
            <input
              id="dept-code"
              type="text"
              value={values.code}
              onChange={(e) => handleChange('code', e.target.value)}
              disabled={saving}
              className={styles.input}
              placeholder="e.g. SCI"
              required
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="dept-type">Type</label>
            <select
              id="dept-type"
              value={values.type}
              onChange={(e) => handleChange('type', e.target.value as DepartmentType)}
              disabled={saving}
              className={styles.select}
            >
              {DEPARTMENT_TYPES.map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
              ))}
            </select>
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
