/**
 * Dashboard: welcome, metrics cards, platform description, nav cards.
 */

import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { fetchContributions } from '@/features/contributions/contributionApi'
import { fetchReportingCycles } from '@/features/reportingCycles/reportingCycleApi'
import type { ApiError } from '@/api/client'
import styles from './DashboardPage.module.css'

const MODULES = [
  { to: '/departments', title: 'Departments', desc: 'Manage organisational units' },
  { to: '/reporting-cycles', title: 'Reporting Cycles', desc: 'Create and open reporting periods' },
  { to: '/contributions', title: 'Contributions', desc: 'View and submit sustainability contributions' },
  { to: '/analytics', title: 'Analytics', desc: 'Summary and breakdowns by cycle' },
  { to: '/report-sections', title: 'Report Sections', desc: 'Draft and export report content' },
  { to: '/exports', title: 'Exports', desc: 'CSV and Markdown exports' },
] as const

type DashboardMetrics = {
  totalContributions: number
  approvedContributions: number
  submittedContributions: number
  draftContributions: number
  activeCycleName: string | null
}

export function DashboardPage() {
  const { user } = useAuth()
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    totalContributions: 0,
    approvedContributions: 0,
    submittedContributions: 0,
    draftContributions: 0,
    activeCycleName: null,
  })
  const [metricsLoading, setMetricsLoading] = useState(true)
  const [metricsError, setMetricsError] = useState<string | null>(null)

  const loadMetrics = useCallback(async () => {
    setMetricsLoading(true)
    setMetricsError(null)
    try {
      const [contributions, cycles] = await Promise.all([
        fetchContributions({}),
        fetchReportingCycles(),
      ])
      const approved = contributions.filter((c) => c.status === 'APPROVED').length
      const submitted = contributions.filter((c) => c.status === 'SUBMITTED').length
      const draft = contributions.filter((c) => c.status === 'DRAFT').length
      const activeCycle = cycles.find((c) => c.status === 'OPEN') ?? null
      setMetrics({
        totalContributions: contributions.length,
        approvedContributions: approved,
        submittedContributions: submitted,
        draftContributions: draft,
        activeCycleName: activeCycle ? activeCycle.name : null,
      })
    } catch (e) {
      const err = e as ApiError
      setMetricsError(err.message || 'Unable to load metrics.')
    } finally {
      setMetricsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadMetrics()
  }, [loadMetrics])

  return (
    <div className={styles.page}>
      <h1 className={styles.welcome}>Welcome{user?.name ? `, ${user.name}` : ''}</h1>
      {user && (
        <p className={styles.role}>
          Signed in as <strong>{user.email}</strong> · Role: {user.role.replace(/_/g, ' ')}
        </p>
      )}

      <section className={styles.metricsSection}>
        <h2 className={styles.metricsTitle}>Overview</h2>
        {metricsLoading && <p className={styles.metricsStatus}>Loading metrics…</p>}
        {metricsError && (
          <p className={styles.metricsError} role="alert">
            {metricsError}
          </p>
        )}
        {!metricsLoading && !metricsError && (
          <div className={styles.metricsGrid}>
            <div className={styles.metricCard}>
              <span className={styles.metricValue}>{metrics.totalContributions}</span>
              <span className={styles.metricLabel}>Total Contributions</span>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricValue}>{metrics.approvedContributions}</span>
              <span className={styles.metricLabel}>Approved Contributions</span>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricValue}>{metrics.submittedContributions}</span>
              <span className={styles.metricLabel}>Submitted Contributions</span>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricValue}>{metrics.draftContributions}</span>
              <span className={styles.metricLabel}>Draft Contributions</span>
            </div>
            <div className={`${styles.metricCard} ${styles.metricCard_cycle}`}>
              <span className={styles.metricValue}>
                {metrics.activeCycleName ?? '—'}
              </span>
              <span className={styles.metricLabel}>Active Reporting Cycle</span>
            </div>
          </div>
        )}
      </section>

      <section className={styles.intro}>
        <h2 className={styles.introTitle}>About this platform</h2>
        <p>
          Sustainability & SDG Reporting Hub helps collect sustainability data from departments,
          map it to the UN Sustainable Development Goals (SDGs), and support reporting and
          AI-assisted draft sections. Use the navigation to access each module.
        </p>
      </section>
      <section className={styles.cards}>
        <h2 className={styles.cardsTitle}>Go to</h2>
        <div className={styles.grid}>
          {MODULES.map(({ to, title, desc }) => (
            <Link key={to} to={to} className={styles.card}>
              <span className={styles.cardTitle}>{title}</span>
              <span className={styles.cardDesc}>{desc}</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
