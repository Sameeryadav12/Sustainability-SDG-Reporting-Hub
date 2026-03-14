import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { AnalyticsSummary } from './analyticsTypes'
import styles from './AnalyticsPage.module.css'

type AnalyticsStatusChartProps = {
  summary: AnalyticsSummary
}

export function AnalyticsStatusChart({ summary }: AnalyticsStatusChartProps) {
  const data = summary.status_breakdown.map((b) => ({
    label: b.status.replace(/_/g, ' '),
    count: b.count,
  }))

  const hasData = data.some((d) => d.count > 0)

  return (
    <section className={styles.chartSection}>
      <h2 className={styles.sectionTitle}>Contributions by Status</h2>
      {!hasData ? (
        <p className={styles.chartEmpty}>No contribution data available for this reporting cycle.</p>
      ) : (
        <div className={styles.chartCard}>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data} margin={{ left: 8, right: 8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#0d9488" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  )
}

