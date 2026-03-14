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

type AnalyticsDepartmentChartProps = {
  summary: AnalyticsSummary
}

export function AnalyticsDepartmentChart({ summary }: AnalyticsDepartmentChartProps) {
  const data = summary.department_breakdown
    .slice()
    .sort((a, b) => (b.count || 0) - (a.count || 0))
    .map((b) => ({
      label: b.department_name || 'No department assigned',
      count: b.count,
    }))

  const hasData = data.some((d) => d.count > 0)

  return (
    <section className={styles.chartSection}>
      <h2 className={styles.sectionTitle}>Contributions by Department</h2>
      {!hasData ? (
        <p className={styles.chartEmpty}>No department data available for this reporting cycle.</p>
      ) : (
        <div className={styles.chartCard}>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data} layout="vertical" margin={{ left: 80, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="label"
                width={140}
                tick={{ fontSize: 11 }}
              />
              <Tooltip />
              <Bar dataKey="count" fill="#7c3aed" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  )
}

