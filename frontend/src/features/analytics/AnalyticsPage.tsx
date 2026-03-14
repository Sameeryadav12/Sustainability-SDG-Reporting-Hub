import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ChangeEvent } from 'react'
import { fetchReportingCycles } from '@/features/reportingCycles/reportingCycleApi'
import type { ReportingCycle } from '@/features/reportingCycles/reportingCycleTypes'
import type { ApiError } from '@/api/client'
import { fetchAnalyticsSummary } from './analyticsApi'
import type { AnalyticsSummary } from './analyticsTypes'
import { AnalyticsSummaryCards } from './AnalyticsSummaryCards'
import { AnalyticsStatusChart } from './AnalyticsStatusChart'
import { AnalyticsSdgChart } from './AnalyticsSdgChart'
import { AnalyticsDepartmentChart } from './AnalyticsDepartmentChart'
import { AnalyticsTypeChart } from './AnalyticsTypeChart'
import styles from './AnalyticsPage.module.css'

export function AnalyticsPage() {
  const [cycles, setCycles] = useState<ReportingCycle[]>([])
  const [selectedCycleId, setSelectedCycleId] = useState<string | ''>('')
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [loadingCycles, setLoadingCycles] = useState(true)
  const [loadingSummary, setLoadingSummary] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadCycles = useCallback(async () => {
    setLoadingCycles(true)
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
      setLoadingCycles(false)
    }
  }, [])

  const loadSummary = useCallback(
    async (cycleId: string) => {
      if (!cycleId) {
        setSummary(null)
        return
      }
      setLoadingSummary(true)
      setError(null)
      try {
        const data = await fetchAnalyticsSummary(cycleId)
        setSummary(data)
      } catch (e) {
        const err = e as ApiError
        const message =
          err.status === 404
            ? 'Reporting cycle not found.'
            : err.message || 'Unable to load analytics.'
        setError(message)
        setSummary(null)
      } finally {
        setLoadingSummary(false)
      }
    },
    []
  )

  useEffect(() => {
    void loadCycles()
  }, [loadCycles])

  useEffect(() => {
    if (selectedCycleId) {
      void loadSummary(selectedCycleId)
    }
  }, [selectedCycleId, loadSummary])

  const handleCycleChange = (e: ChangeEvent<HTMLSelectElement>) => {
    setSelectedCycleId(e.target.value)
  }

  const selectedCycle = useMemo(
    () => cycles.find((c) => c.id === selectedCycleId) ?? null,
    [cycles, selectedCycleId]
  )

  const isLoading = loadingCycles || loadingSummary

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Analytics</h1>
        {cycles.length > 0 && (
          <div className={styles.cycleSelector}>
            <label htmlFor="analytics-cycle">Reporting cycle</label>
            <select
              id="analytics-cycle"
              className={styles.cycleSelect}
              value={selectedCycleId}
              onChange={handleCycleChange}
            >
              {cycles.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name || `${c.year}`}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loadingCycles && <p className={styles.statusText}>Loading reporting cycles…</p>}
      {!loadingCycles && cycles.length === 0 && !error && (
        <p className={styles.statusText}>No reporting cycles available.</p>
      )}

      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      {!error && selectedCycle && summary && (
        <>
          <AnalyticsSummaryCards summary={summary} />

          {isLoading && <p className={styles.statusText}>Loading analytics…</p>}

          {!isLoading && (
            <div className={styles.chartsGrid}>
              <AnalyticsStatusChart summary={summary} />
              <AnalyticsTypeChart summary={summary} />
              <AnalyticsSdgChart summary={summary} />
              <AnalyticsDepartmentChart summary={summary} />
            </div>
          )}
        </>
      )}

      {!error && selectedCycle && !summary && !isLoading && (
        <p className={styles.statusText}>
          No contribution data available for this reporting cycle.
        </p>
      )}
    </div>
  )
}

