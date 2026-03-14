import type { AnalyticsSummary } from './analyticsTypes'
import styles from './AnalyticsPage.module.css'

type AnalyticsSummaryCardsProps = {
  summary: AnalyticsSummary
}

export function AnalyticsSummaryCards({ summary }: AnalyticsSummaryCardsProps) {
  const metricsCount =
    typeof summary.metrics_count === 'number' && summary.metrics_count >= 0
      ? summary.metrics_count
      : null

  return (
    <section className={styles.summarySection}>
      <h2 className={styles.sectionTitle}>Summary</h2>
      <div className={styles.summaryGrid}>
        <div className={styles.summaryCard}>
          <span className={styles.summaryValue}>{summary.total_contributions}</span>
          <span className={styles.summaryLabel}>Total Contributions</span>
        </div>
        <div className={styles.summaryCard}>
          <span className={styles.summaryValue}>{summary.departments_with_contributions}</span>
          <span className={styles.summaryLabel}>Departments With Contributions</span>
        </div>
        <div className={styles.summaryCard}>
          <span className={styles.summaryValue}>{summary.sdgs_covered}</span>
          <span className={styles.summaryLabel}>SDGs Covered</span>
        </div>
        {metricsCount !== null && (
          <div className={styles.summaryCard}>
            <span className={styles.summaryValue}>{metricsCount}</span>
            <span className={styles.summaryLabel}>Metrics Count</span>
          </div>
        )}
        <div className={styles.summaryCard}>
          <span className={styles.summaryValue}>
            {summary.status_breakdown.find((b) => b.status === 'APPROVED')?.count ?? 0}
          </span>
          <span className={styles.summaryLabel}>Approved Contributions</span>
        </div>
      </div>
    </section>
  )
}

