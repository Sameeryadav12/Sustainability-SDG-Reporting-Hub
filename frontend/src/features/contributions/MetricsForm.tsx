import { useCallback, useEffect, useState } from 'react'
import type { ApiError } from '@/api/client'
import { fetchMetrics, createMetric, deleteMetric } from './metricsApi'
import type { Metric, MetricCreate } from './metricsApi'
import styles from './ContributionsPage.module.css'

type MetricsFormProps = {
  contributionId: string
  canEdit: boolean
  onLoad?: () => void
}

export function MetricsForm({ contributionId, canEdit, onLoad }: MetricsFormProps) {
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metricName, setMetricName] = useState('')
  const [metricValue, setMetricValue] = useState('')
  const [unit, setUnit] = useState('')
  const [year, setYear] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const list = await fetchMetrics(contributionId)
      setMetrics(list)
      onLoad?.()
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to load metrics.')
    } finally {
      setLoading(false)
    }
  }, [contributionId, onLoad])

  useEffect(() => {
    load()
  }, [load])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canEdit) return
    const name = metricName.trim()
    if (!name) return
    const valStr = metricValue.trim()
    if (!valStr) return
    const numVal = parseFloat(valStr)
    const isNum = !isNaN(numVal)
    setSubmitting(true)
    setError(null)
    try {
      const data: MetricCreate = {
        name,
        value_number: isNum ? numVal : null,
        value_text: isNum ? null : valStr,
        unit: unit.trim() || undefined,
        year: year.trim() ? parseInt(year, 10) : undefined,
      }
      await createMetric(contributionId, data)
      setMetricName('')
      setMetricValue('')
      setUnit('')
      setYear('')
      await load()
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Failed to add metric.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!canEdit) return
    setDeletingId(id)
    setError(null)
    try {
      await deleteMetric(id)
      await load()
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Failed to delete metric.')
    } finally {
      setDeletingId(null)
    }
  }

  const formatValue = (m: Metric): string => {
    if (m.value_number != null) {
      const parts = [String(m.value_number)]
      if (m.unit) parts.push(m.unit)
      if (m.year) parts.push(`(${m.year})`)
      return parts.join(' ')
    }
    return m.value_text || '—'
  }

  if (loading) return <p className={styles.loading}>Loading metrics…</p>
  if (error) return <p className={styles.error}>{error}</p>

  return (
    <div>
      <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1rem' }}>
        {metrics.map((m) => (
          <li
            key={m.id}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '0.5rem 0',
              borderBottom: '1px solid #e5e7eb',
            }}
          >
            <span>
              <strong>{m.name}</strong>: {formatValue(m)}
            </span>
            {canEdit && (
              <button
                type="button"
                className={styles.linkBtn}
                onClick={() => handleDelete(m.id)}
                disabled={deletingId === m.id}
              >
                {deletingId === m.id ? 'Deleting…' : 'Delete'}
              </button>
            )}
          </li>
        ))}
      </ul>
      {metrics.length === 0 && <p className={styles.empty}>No metrics yet.</p>}
      {canEdit && (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'flex-end' }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>Metric name</span>
            <input
              type="text"
              value={metricName}
              onChange={(e) => setMetricName(e.target.value)}
              placeholder="e.g. Students reached"
              required
              minLength={2}
              maxLength={120}
              style={{ padding: '0.4rem 0.6rem', border: '1px solid #d1d5db', borderRadius: '6px', width: 140 }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>Value</span>
            <input
              type="text"
              value={metricValue}
              onChange={(e) => setMetricValue(e.target.value)}
              placeholder="e.g. 150 or text"
              required
              style={{ padding: '0.4rem 0.6rem', border: '1px solid #d1d5db', borderRadius: '6px', width: 120 }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>Unit</span>
            <input
              type="text"
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              placeholder="e.g. students"
              style={{ padding: '0.4rem 0.6rem', border: '1px solid #d1d5db', borderRadius: '6px', width: 100 }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>Year</span>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              placeholder="e.g. 2024"
              min={2000}
              max={2100}
              style={{ padding: '0.4rem 0.6rem', border: '1px solid #d1d5db', borderRadius: '6px', width: 80 }}
            />
          </label>
          <button type="submit" className={styles.primaryBtn} disabled={submitting}>
            {submitting ? 'Adding…' : 'Add metric'}
          </button>
        </form>
      )}
    </div>
  )
}
