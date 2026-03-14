/**
 * Exports page: CSV and Markdown export for selected reporting cycle.
 */

import { useCallback, useEffect, useState } from 'react'
import type { ChangeEvent } from 'react'
import { fetchReportingCycles } from '@/features/reportingCycles/reportingCycleApi'
import type { ReportingCycle } from '@/features/reportingCycles/reportingCycleTypes'
import {
  downloadContributionsCsv,
  downloadMetricsCsv,
  downloadEvidenceCsv,
  fetchMarkdownReport,
} from './exportsApi'
import { ReportMarkdownPreview } from '@/features/reportSections/ReportMarkdownPreview'
import type { ApiError } from '@/api/client'
import styles from './ExportsPage.module.css'

export function ExportsPage() {
  const [cycles, setCycles] = useState<ReportingCycle[]>([])
  const [selectedCycleId, setSelectedCycleId] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeExport, setActiveExport] = useState<string | null>(null)
  const [markdownPreview, setMarkdownPreview] = useState<{
    reporting_cycle_id: string
    cycle_name: string
    cycle_year: number
    section_count: number
    content_markdown: string
  } | null>(null)

  const loadCycles = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const list = await fetchReportingCycles()
      setCycles(list)
      if (list.length > 0) {
        const open = list.find((c) => c.status === 'OPEN')
        const latest =
          open ??
          [...list].sort((a, b) => {
            if (a.year !== b.year) return b.year - a.year
            return a.start_date.localeCompare(b.start_date)
          })[0]
        setSelectedCycleId(latest?.id ?? list[0]?.id ?? '')
      } else {
        setSelectedCycleId('')
      }
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to load reporting cycles.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadCycles()
  }, [loadCycles])

  const handleCycleChange = (e: ChangeEvent<HTMLSelectElement>) => {
    setSelectedCycleId(e.target.value)
  }

  const handleContributionsCsv = async () => {
    if (!selectedCycleId) return
    setActiveExport('contributions')
    setError(null)
    try {
      await downloadContributionsCsv(selectedCycleId)
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to export contributions CSV.')
    } finally {
      setActiveExport(null)
    }
  }

  const handleMetricsCsv = async () => {
    if (!selectedCycleId) return
    setActiveExport('metrics')
    setError(null)
    try {
      await downloadMetricsCsv(selectedCycleId)
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to export metrics CSV.')
    } finally {
      setActiveExport(null)
    }
  }

  const handleEvidenceCsv = async () => {
    if (!selectedCycleId) return
    setActiveExport('evidence')
    setError(null)
    try {
      await downloadEvidenceCsv(selectedCycleId)
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to export evidence CSV.')
    } finally {
      setActiveExport(null)
    }
  }

  const handlePreviewMarkdown = async () => {
    if (!selectedCycleId) return
    setActiveExport('markdown')
    setError(null)
    try {
      const report = await fetchMarkdownReport(selectedCycleId)
      setMarkdownPreview(report)
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to load Markdown report.')
    } finally {
      setActiveExport(null)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Exports</h1>
        {cycles.length > 0 && (
          <div className={styles.cycleSelector}>
            <label htmlFor="exports-cycle">Reporting cycle</label>
            <select
              id="exports-cycle"
              className={styles.cycleSelect}
              value={selectedCycleId}
              onChange={handleCycleChange}
            >
              {cycles.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name || c.year}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loading && <p className={styles.loadingText}>Loading reporting cycles…</p>}
      {!loading && cycles.length === 0 && !error && (
        <p className={styles.statusText}>No reporting cycles available for export.</p>
      )}
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      {selectedCycleId && !loading && (
        <>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>CSV Exports</h2>
            <div className={styles.cardsGrid}>
              <div className={styles.card}>
                <span className={styles.cardTitle}>Export Contributions CSV</span>
                <span className={styles.cardDesc}>
                  Download contribution records for the selected reporting cycle.
                </span>
                <button
                  type="button"
                  onClick={handleContributionsCsv}
                  disabled={!!activeExport}
                  className={styles.primaryBtn}
                >
                  {activeExport === 'contributions' ? 'Exporting…' : 'Download CSV'}
                </button>
              </div>
              <div className={styles.card}>
                <span className={styles.cardTitle}>Export Metrics CSV</span>
                <span className={styles.cardDesc}>
                  Download contribution metrics for the selected reporting cycle.
                </span>
                <button
                  type="button"
                  onClick={handleMetricsCsv}
                  disabled={!!activeExport}
                  className={styles.primaryBtn}
                >
                  {activeExport === 'metrics' ? 'Exporting…' : 'Download CSV'}
                </button>
              </div>
              <div className={styles.card}>
                <span className={styles.cardTitle}>Export Evidence CSV</span>
                <span className={styles.cardDesc}>
                  Download uploaded evidence metadata for the selected reporting cycle.
                </span>
                <button
                  type="button"
                  onClick={handleEvidenceCsv}
                  disabled={!!activeExport}
                  className={styles.primaryBtn}
                >
                  {activeExport === 'evidence' ? 'Exporting…' : 'Download CSV'}
                </button>
              </div>
            </div>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Report Export</h2>
            <div className={styles.cardsGrid}>
              <div className={styles.card}>
                <span className={styles.cardTitle}>Markdown Report</span>
                <span className={styles.cardDesc}>
                  Preview or download the compiled report draft for the selected cycle.
                </span>
                <button
                  type="button"
                  onClick={handlePreviewMarkdown}
                  disabled={!!activeExport}
                  className={styles.primaryBtn}
                >
                  {activeExport === 'markdown' ? 'Loading…' : 'Preview Markdown'}
                </button>
              </div>
            </div>
          </section>
        </>
      )}

      {markdownPreview && (
        <ReportMarkdownPreview
          report={markdownPreview}
          onClose={() => setMarkdownPreview(null)}
        />
      )}
    </div>
  )
}
