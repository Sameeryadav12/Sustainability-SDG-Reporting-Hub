/**
 * Modal to preview compiled Markdown report for a cycle.
 */

import type { CompiledReportResponse } from './reportSectionsTypes'
import styles from './ReportSectionsPage.module.css'

type ReportMarkdownPreviewProps = {
  report: CompiledReportResponse
  onClose: () => void
}

export function ReportMarkdownPreview({ report, onClose }: ReportMarkdownPreviewProps) {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(report.content_markdown)
      // Could add a small toast; for now we just copy silently
    } catch {
      // ignore
    }
  }

  const handleDownload = () => {
    const blob = new Blob([report.content_markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${report.cycle_name.replace(/\s+/g, '_')}_${report.cycle_year}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className={styles.backdrop} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modal} onClick={(e) => e.stopPropagation()} style={{ maxWidth: 800 }}>
        <header className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>Preview Markdown Report</h2>
          <p className={styles.markdownPreviewMeta}>
            {report.cycle_name} ({report.cycle_year}) · {report.section_count} section(s)
          </p>
        </header>
        <div className={styles.modalBody}>
          <pre className={styles.markdownPreview}>{report.content_markdown || '(No content)'}</pre>
          <div className={styles.previewActions}>
            <button type="button" onClick={handleCopy} className={styles.secondaryBtn}>
              Copy to clipboard
            </button>
            <button type="button" onClick={handleDownload} className={styles.primaryBtn}>
              Download .md
            </button>
          </div>
        </div>
        <footer className={styles.modalFooter}>
          <button type="button" onClick={onClose} className={styles.secondaryBtn}>
            Close
          </button>
        </footer>
      </div>
    </div>
  )
}
