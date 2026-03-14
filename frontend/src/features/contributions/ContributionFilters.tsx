import { useMemo } from 'react'
import type { ChangeEvent } from 'react'
import type { ContributionFilters } from './contributionTypes'
import type { ReportingCycle } from '@/features/reportingCycles/reportingCycleTypes'
import type { Department } from '@/features/departments/departmentTypes'
import { SDG_IDS } from './contributionTypes'
import styles from './ContributionsPage.module.css'

type ContributionFiltersProps = {
  value: ContributionFilters
  onChange: (next: ContributionFilters) => void
  reportingCycles: ReportingCycle[]
  departments: Department[]
}

const STATUS_OPTIONS = ['DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED'] as const
const TYPE_OPTIONS = ['RESEARCH', 'TEACHING', 'OPERATIONS', 'POLICY', 'COMMUNITY', 'OTHER'] as const

export function ContributionFilters({
  value,
  onChange,
  reportingCycles,
  departments,
}: ContributionFiltersProps) {
  const handleSelectChange =
    (field: keyof ContributionFilters) =>
    (e: ChangeEvent<HTMLSelectElement>) => {
      const v = e.target.value
      const next: ContributionFilters = { ...value }
      if (!v) {
        delete (next as Record<string, unknown>)[field]
      } else if (field === 'sdg') {
        next.sdg = Number(v)
      } else {
        ;(next as Record<string, unknown>)[field] = v
      }
      onChange(next)
    }

  const cycleOptions = useMemo(
    () =>
      reportingCycles.map((c) => ({
        id: c.id,
        label: c.name || String(c.year),
      })),
    [reportingCycles]
  )

  const departmentOptions = useMemo(
    () =>
      departments.map((d) => ({
        id: d.id,
        label: d.name,
      })),
    [departments]
  )

  return (
    <section className={styles.filters}>
      <div className={styles.filterRow}>
        <label className={styles.filterField}>
          <span>Reporting cycle</span>
          <select
            value={value.reporting_cycle_id ?? ''}
            onChange={handleSelectChange('reporting_cycle_id')}
          >
            <option value="">All</option>
            {cycleOptions.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
        <label className={styles.filterField}>
          <span>Department</span>
          <select
            value={value.department_id ?? ''}
            onChange={handleSelectChange('department_id')}
          >
            <option value="">All</option>
            {departmentOptions.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </select>
        </label>
        <label className={styles.filterField}>
          <span>SDG</span>
          <select value={value.sdg ?? ''} onChange={handleSelectChange('sdg')}>
            <option value="">All</option>
            {SDG_IDS.map((id) => (
              <option key={id} value={id}>
                SDG {id}
              </option>
            ))}
          </select>
        </label>
        <label className={styles.filterField}>
          <span>Status</span>
          <select value={value.status ?? ''} onChange={handleSelectChange('status')}>
            <option value="">All</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className={styles.filterField}>
          <span>Type</span>
          <select value={value.type ?? ''} onChange={handleSelectChange('type')}>
            <option value="">All</option>
            {TYPE_OPTIONS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  )
}

