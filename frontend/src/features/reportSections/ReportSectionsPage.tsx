/**
 * Report Sections page: list, create, edit, AI generate, Markdown preview.
 */

import { useCallback, useEffect, useState } from 'react'
import type { ChangeEvent } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { fetchReportingCycles } from '@/features/reportingCycles/reportingCycleApi'
import type { ReportingCycle } from '@/features/reportingCycles/reportingCycleTypes'
import { fetchDepartments } from '@/features/departments/departmentApi'
import type { Department } from '@/features/departments/departmentTypes'
import {
  fetchReportSections,
  fetchReportSection,
  createReportSection,
  updateReportSection,
  generateReportSection,
  fetchMarkdownReport,
} from './reportSectionsApi'
import type {
  ReportSectionListItem,
  ReportSection,
  ReportSectionCreate,
  ReportSectionGenerateRequest,
  CompiledReportResponse,
} from './reportSectionsTypes'
import { ReportSectionForm } from './ReportSectionForm'
import { ReportSectionEditor } from './ReportSectionEditor'
import { ReportSectionGenerateForm } from './ReportSectionGenerateForm'
import { ReportMarkdownPreview } from './ReportMarkdownPreview'
import type { ApiError } from '@/api/client'
import styles from './ReportSectionsPage.module.css'

const ROLE_ADMIN = 'ADMIN'

function formatDate(s: string | null | undefined): string {
  if (!s) return '—'
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

function formatScopeDisplay(
  scopeType: string,
  scopeValue: string,
  departments: Department[]
): string {
  if (scopeType === 'DEPARTMENT' && scopeValue) {
    const dept = departments.find((d) => d.id === scopeValue)
    return dept ? dept.name : scopeValue
  }
  if (scopeType === 'OVERALL') return 'Overall'
  if (scopeType === 'SDG' && scopeValue) return `SDG ${scopeValue}`
  if (scopeType === 'THEME') return scopeValue || 'Theme'
  return scopeValue || scopeType
}

export function ReportSectionsPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === ROLE_ADMIN

  const [cycles, setCycles] = useState<ReportingCycle[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [selectedCycleId, setSelectedCycleId] = useState<string>('')
  const [sections, setSections] = useState<ReportSectionListItem[]>([])
  const [loadingCycles, setLoadingCycles] = useState(true)
  const [loadingSections, setLoadingSections] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [generateModalOpen, setGenerateModalOpen] = useState(false)
  const [editingSection, setEditingSection] = useState<ReportSection | null>(null)
  const [markdownPreview, setMarkdownPreview] = useState<CompiledReportResponse | null>(null)
  const [loadingMarkdown, setLoadingMarkdown] = useState(false)

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

  const loadDepartments = useCallback(async () => {
    try {
      const list = await fetchDepartments()
      setDepartments(list)
    } catch {
      setDepartments([])
    }
  }, [])

  const loadSections = useCallback(
    async (cycleId: string) => {
      if (!cycleId) {
        setSections([])
        return
      }
      setLoadingSections(true)
      setError(null)
      try {
        const list = await fetchReportSections(cycleId)
        setSections(list)
      } catch (e) {
        const err = e as ApiError
        setError(err.message || 'Unable to load report sections.')
        setSections([])
      } finally {
        setLoadingSections(false)
      }
    },
    []
  )

  useEffect(() => {
    void loadCycles()
    void loadDepartments()
  }, [loadCycles, loadDepartments])

  useEffect(() => {
    if (selectedCycleId) void loadSections(selectedCycleId)
    else setSections([])
  }, [selectedCycleId, loadSections])

  const handleCycleChange = (e: ChangeEvent<HTMLSelectElement>) => {
    setSelectedCycleId(e.target.value)
  }

  const handleCreateSubmit = async (data: ReportSectionCreate) => {
    await createReportSection(data)
    if (selectedCycleId) await loadSections(selectedCycleId)
  }

  const handleEditSubmit = async (
    id: string,
    data: { title: string; content_markdown: string; status: ReportSectionListItem['status'] }
  ) => {
    await updateReportSection(id, data)
    setEditingSection(null)
    if (selectedCycleId) await loadSections(selectedCycleId)
  }

  const handleGenerateSubmit = async (data: ReportSectionGenerateRequest) => {
    await generateReportSection(data)
    setGenerateModalOpen(false)
    if (selectedCycleId) await loadSections(selectedCycleId)
  }

  const openEditor = async (item: ReportSectionListItem) => {
    if (!isAdmin) return
    try {
      const full = await fetchReportSection(item.id)
      setEditingSection(full)
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to load report section.')
    }
  }

  const handlePreviewMarkdown = async () => {
    if (!selectedCycleId) return
    setLoadingMarkdown(true)
    setError(null)
    try {
      const report = await fetchMarkdownReport(selectedCycleId)
      setMarkdownPreview(report)
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to load Markdown report.')
    } finally {
      setLoadingMarkdown(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Report Sections</h1>
        <div className={styles.headerActions}>
          {cycles.length > 0 && (
            <div className={styles.cycleSelector}>
              <label htmlFor="rs-cycle">Reporting cycle</label>
              <select
                id="rs-cycle"
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
          {selectedCycleId && (
            <>
              <button
                type="button"
                onClick={handlePreviewMarkdown}
                disabled={loadingMarkdown}
                className={styles.secondaryBtn}
              >
                {loadingMarkdown ? 'Loading…' : 'Preview Markdown'}
              </button>
              {isAdmin && (
                <>
                  <button
                    type="button"
                    onClick={() => setCreateModalOpen(true)}
                    className={styles.primaryBtn}
                  >
                    New report section
                  </button>
                  <button
                    type="button"
                    onClick={() => setGenerateModalOpen(true)}
                    className={styles.secondaryBtn}
                  >
                    Generate with AI
                  </button>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {loadingCycles && <p className={styles.loadingText}>Loading reporting cycles…</p>}
      {!loadingCycles && cycles.length === 0 && !error && (
        <p className={styles.statusText}>No reporting cycles available.</p>
      )}
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      {selectedCycleId && (
        <>
          {loadingSections && <p className={styles.loadingText}>Loading report sections…</p>}
          {!loadingSections && sections.length === 0 && !error && (
            <p className={styles.statusText}>No report sections found for this cycle.</p>
          )}
          {!loadingSections && sections.length > 0 && (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Scope</th>
                    <th>Status</th>
                    <th>Generated by</th>
                    <th>Updated</th>
                    {isAdmin && <th className={styles.actionsCol} />}
                  </tr>
                </thead>
                <tbody>
                  {sections.map((s) => (
                    <tr key={s.id}>
                      <td>{s.title}</td>
                      <td>
                        {s.scope_type} / {formatScopeDisplay(s.scope_type, s.scope_value, departments)}
                      </td>
                      <td>
                        <span className={styles[`badge_${s.status}`] ?? styles.badge}>
                          {s.status}
                        </span>
                      </td>
                      <td>{s.generated_by}</td>
                      <td>{formatDate(s.updated_at)}</td>
                      {isAdmin && (
                        <td className={styles.actionsCol}>
                          <button
                            type="button"
                            onClick={() => openEditor(s)}
                            className={styles.linkBtn}
                          >
                            Edit
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {createModalOpen && selectedCycleId && (
        <ReportSectionForm
          reportingCycleId={selectedCycleId}
          departments={departments}
          onClose={() => setCreateModalOpen(false)}
          onSubmit={handleCreateSubmit}
        />
      )}

      {generateModalOpen && selectedCycleId && (
        <ReportSectionGenerateForm
          reportingCycleId={selectedCycleId}
          departments={departments}
          onClose={() => setGenerateModalOpen(false)}
          onSubmit={handleGenerateSubmit}
        />
      )}

      {editingSection && (
        <ReportSectionEditor
          section={editingSection}
          departments={departments}
          onClose={() => setEditingSection(null)}
          onSubmit={handleEditSubmit}
        />
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
