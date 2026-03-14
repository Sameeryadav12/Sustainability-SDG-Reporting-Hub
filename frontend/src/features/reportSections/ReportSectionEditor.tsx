/**
 * Editor modal for editing an existing report section (admin only).
 */

import { useState, useEffect, type FormEvent } from 'react'
import type { ReportSection, ReportSectionStatus } from './reportSectionsTypes'
import { SECTION_STATUSES } from './reportSectionsTypes'
import type { Department } from '@/features/departments/departmentTypes'
import type { ApiError } from '@/api/client'
import styles from './ReportSectionsPage.module.css'

function formatScopeDisplay(scopeType: string, scopeValue: string, departments: Department[]): string {
  if (scopeType === 'DEPARTMENT' && scopeValue) {
    const dept = departments.find((d) => d.id === scopeValue)
    return dept ? dept.name : scopeValue
  }
  if (scopeType === 'OVERALL') return 'Overall'
  if (scopeType === 'SDG' && scopeValue) return `SDG ${scopeValue}`
  if (scopeType === 'THEME') return scopeValue || 'Theme'
  return scopeValue || scopeType
}

type ReportSectionEditorProps = {
  section: ReportSection
  departments: Department[]
  onClose: () => void
  onSubmit: (id: string, data: { title: string; content_markdown: string; status: ReportSectionStatus }) => Promise<void>
}

export function ReportSectionEditor({ section, departments, onClose, onSubmit }: ReportSectionEditorProps) {
  const [title, setTitle] = useState(section.title)
  const [contentMarkdown, setContentMarkdown] = useState(section.content_markdown)
  const [status, setStatus] = useState<ReportSectionStatus>(section.status)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setTitle(section.title)
    setContentMarkdown(section.content_markdown)
    setStatus(section.status)
  }, [section])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    const t = title.trim()
    const c = contentMarkdown.trim()
    if (!t || t.length < 3) {
      setError('Title must be at least 3 characters.')
      return
    }
    if (!c) {
      setError('Content (Markdown) is required.')
      return
    }
    setSaving(true)
    try {
      await onSubmit(section.id, { title: t, content_markdown: c, status })
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
          <h2 className={styles.modalTitle}>Edit report section</h2>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: '#6b7280' }}>
            {section.scope_type} / {formatScopeDisplay(section.scope_type, section.scope_value, departments)}
          </p>
        </header>
        <form onSubmit={handleSubmit}>
        <div className={styles.modalBody}>
          {error && <p className={styles.formError} role="alert">{error}</p>}
          <div className={styles.field}>
            <label>Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              minLength={3}
            />
          </div>
          <div className={styles.field}>
            <label>Content (Markdown)</label>
            <textarea
              value={contentMarkdown}
              onChange={(e) => setContentMarkdown(e.target.value)}
              required
              style={{ minHeight: 200 }}
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
            {saving ? 'Saving…' : 'Save'}
          </button>
        </footer>
        </form>
      </div>
    </div>
  )
}
