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

type AnalyticsSdgChartProps = {
  summary: AnalyticsSummary
}

export function AnalyticsSdgChart({ summary }: AnalyticsSdgChartProps) {
  const data = summary.sdg_breakdown
    .slice()
    .sort((a, b) => a.sdg - b.sdg)
    .map((b) => ({
      label: `SDG ${b.sdg}`,
      count: b.count,
    }))

  const hasData = data.some((d) => d.count > 0)

  return (
    <section className={styles.chartSection}>
      <h2 className={styles.sectionTitle}>Contributions by SDG</h2>
      {!hasData ? (
        <p className={styles.chartEmpty}>No SDG data available for this reporting cycle.</p>
      ) : (
        <div className={styles.chartCard}>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data} layout="vertical" margin={{ left: 40, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="label"
                width={70}
                tick={{ fontSize: 11 }}
              />
              <Tooltip />
              <Bar dataKey="count" fill="#2563eb" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  )
}

