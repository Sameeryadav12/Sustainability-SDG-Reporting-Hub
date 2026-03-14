/**
 * Form for AI report section generation (admin only).
 */

import { useState, useEffect, type FormEvent } from 'react'
import type { ReportSectionScopeType } from './reportSectionsTypes'
import { SCOPE_TYPES, SDG_IDS } from './reportSectionsTypes'
import type { Department } from '@/features/departments/departmentTypes'
import type { ReportSectionGenerateRequest } from './reportSectionsTypes'
import type { ApiError } from '@/api/client'
import styles from './ReportSectionsPage.module.css'

type ReportSectionGenerateFormProps = {
  reportingCycleId: string
  departments: Department[]
  onClose: () => void
  onSubmit: (data: ReportSectionGenerateRequest) => Promise<void>
}

export function ReportSectionGenerateForm({
  reportingCycleId,
  departments,
  onClose,
  onSubmit,
}: ReportSectionGenerateFormProps) {
  const [scopeType, setScopeType] = useState<ReportSectionScopeType>('SDG')
  const [scopeValue, setScopeValue] = useState('1')
  const [title, setTitle] = useState('')
  const [targetWordCount, setTargetWordCount] = useState(500)
  const [overwriteExisting, setOverwriteExisting] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    if (scopeType === 'SDG') setScopeValue('1')
    if (scopeType === 'DEPARTMENT' && departments.length > 0) setScopeValue(departments[0]?.id ?? '')
    if (scopeType === 'OVERALL') setScopeValue('summary')
    if (scopeType === 'THEME') setScopeValue('')
  }, [scopeType, departments])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    const sv = scopeValue.trim()
    if (!sv) {
      setError('Scope value is required.')
      return
    }
    if (targetWordCount < 100 || targetWordCount > 1200) {
      setError('Target word count must be between 100 and 1200.')
      return
    }
    setGenerating(true)
    try {
      await onSubmit({
        reporting_cycle_id: reportingCycleId,
        scope_type: scopeType,
        scope_value: sv,
        title: title.trim() || undefined,
        target_word_count: targetWordCount,
        overwrite_existing: overwriteExisting,
      })
      onClose()
    } catch (e) {
      const err = e as ApiError
      const msg = err.message || 'Unable to generate report section.'
      if (
        msg.toLowerCase().includes('no relevant data') ||
        msg.toLowerCase().includes('not found')
      ) {
        setError('No relevant data found for this generation scope.')
      } else if (
        msg.toLowerCase().includes('not configured') ||
        msg.toLowerCase().includes('openai_api_key')
      ) {
        setError(
          `${msg} To enable AI generation, add OPENAI_API_KEY to the backend .env file (in the backend folder) and restart the API.`
        )
      } else if (msg.toLowerCase().includes('failed') || msg.toLowerCase().includes('unavailable')) {
        setError('Report section generation failed. Please try again.')
      } else {
        setError(msg)
      }
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className={styles.backdrop} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <header className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>Generate with AI</h2>
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
                <input type="text" value="summary" readOnly disabled />
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
            <label>Title (optional)</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Leave empty to auto-generate"
            />
          </div>
          <div className={styles.field}>
            <label>Target word count (100–1200)</label>
            <input
              type="number"
              min={100}
              max={1200}
              value={targetWordCount}
              onChange={(e) => setTargetWordCount(Number(e.target.value) || 500)}
            />
          </div>
          <div className={styles.field}>
            <label>
              <input
                type="checkbox"
                checked={overwriteExisting}
                onChange={(e) => setOverwriteExisting(e.target.checked)}
              />
              {' '}
              Overwrite existing section for this scope
            </label>
          </div>
        </div>
        <footer className={styles.modalFooter}>
          <button type="button" onClick={onClose} className={styles.secondaryBtn} disabled={generating}>
            Cancel
          </button>
          <button type="submit" className={styles.primaryBtn} disabled={generating}>
            {generating ? 'Generating…' : 'Generate'}
          </button>
        </footer>
        </form>
      </div>
    </div>
  )
}
