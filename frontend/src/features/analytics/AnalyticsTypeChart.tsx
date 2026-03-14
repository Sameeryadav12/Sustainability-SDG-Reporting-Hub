import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import type { AnalyticsSummary } from './analyticsTypes'
import styles from './AnalyticsPage.module.css'

type AnalyticsTypeChartProps = {
  summary: AnalyticsSummary
}

const TYPE_COLORS: Record<string, string> = {
  RESEARCH: '#0ea5e9',
  TEACHING: '#22c55e',
  OPERATIONS: '#f97316',
  POLICY: '#6366f1',
  COMMUNITY: '#ec4899',
  OTHER: '#6b7280',
}

export function AnalyticsTypeChart({ summary }: AnalyticsTypeChartProps) {
  const data = summary.type_breakdown
    .slice()
    .filter((b) => b.count > 0)
    .map((b) => ({
      label: b.type.replace(/_/g, ' '),
      type: b.type,
      count: b.count,
    }))

  const hasData = data.length > 0

  return (
    <section className={styles.chartSection}>
      <h2 className={styles.sectionTitle}>Contributions by Type</h2>
      {!hasData ? (
        <p className={styles.chartEmpty}>No type data available for this reporting cycle.</p>
      ) : (
        <div className={styles.chartCard}>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={data}
                dataKey="count"
                nameKey="label"
                cx="50%"
                cy="50%"
                outerRadius={90}
                innerRadius={40}
                paddingAngle={2}
              >
                {data.map((entry) => (
                  <Cell
                    key={entry.type}
                    fill={TYPE_COLORS[entry.type] ?? TYPE_COLORS.OTHER}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  )
}

