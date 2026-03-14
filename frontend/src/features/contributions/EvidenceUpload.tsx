import { useCallback, useEffect, useRef, useState } from 'react'
import { getApiBaseUrl } from '@/api/client'
import type { ApiError } from '@/api/client'
import { fetchEvidence, uploadEvidence, deleteEvidence } from './evidenceApi'
import type { EvidenceFile } from './evidenceApi'
import styles from './ContributionsPage.module.css'

const ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx', 'csv']
const MAX_SIZE_MB = 10

function getExtension(name: string): string {
  const i = name.lastIndexOf('.')
  return i >= 0 ? name.slice(i + 1).toLowerCase() : ''
}

function isAllowedType(file: File): boolean {
  const ext = getExtension(file.name)
  return ALLOWED_EXTENSIONS.includes(ext)
}

type EvidenceUploadProps = {
  contributionId: string
  canEdit: boolean
  onLoad?: () => void
}

export function EvidenceUpload({ contributionId, canEdit, onLoad }: EvidenceUploadProps) {
  const [evidence, setEvidence] = useState<EvidenceFile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const list = await fetchEvidence(contributionId)
      setEvidence(list)
      onLoad?.()
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to load evidence.')
    } finally {
      setLoading(false)
    }
  }, [contributionId, onLoad])

  useEffect(() => {
    load()
  }, [load])

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    if (!canEdit) return
    setError(null)
    if (!isAllowedType(file)) {
      setError('This file type is not allowed.')
      return
    }
    const maxBytes = MAX_SIZE_MB * 1024 * 1024
    if (file.size > maxBytes) {
      setError('The selected file is too large.')
      return
    }
    setUploading(true)
    try {
      await uploadEvidence(contributionId, file)
      await load()
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr.message || 'Unable to upload evidence.')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!canEdit) return
    setDeletingId(id)
    setError(null)
    try {
      await deleteEvidence(id)
      await load()
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Failed to delete evidence.')
    } finally {
      setDeletingId(null)
    }
  }

  const fileUrl = (e: EvidenceFile): string => {
    const url = e.file_url
    if (url.startsWith('http')) return url
    const base = getApiBaseUrl().replace(/\/api\/v1$/, '')
    return url.startsWith('/') ? `${base}${url}` : `${base}/${url}`
  }

  if (loading) return <p className={styles.loading}>Loading evidence…</p>
  if (error) return <p className={styles.error}>{error}</p>

  return (
    <div>
      <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1rem' }}>
        {evidence.map((e) => (
          <li
            key={e.id}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '0.5rem 0',
              borderBottom: '1px solid #e5e7eb',
            }}
          >
            <span>
              <a
                href={fileUrl(e)}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.linkBtn}
                style={{ textDecoration: 'underline' }}
              >
                {e.file_name}
              </a>
              {e.uploaded_at && (
                <span style={{ fontSize: '0.8rem', color: '#6b7280', marginLeft: '0.5rem' }}>
                  {new Date(e.uploaded_at).toLocaleDateString()}
                </span>
              )}
            </span>
            {canEdit && (
              <button
                type="button"
                className={styles.linkBtn}
                onClick={() => handleDelete(e.id)}
                disabled={deletingId === e.id}
              >
                {deletingId === e.id ? 'Deleting…' : 'Delete'}
              </button>
            )}
          </li>
        ))}
      </ul>
      {evidence.length === 0 && <p className={styles.empty}>No evidence files yet.</p>}
      {canEdit && (
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.xlsx,.xls,.csv,.jpg,.jpeg,.png,.doc,.docx"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          <button
            type="button"
            className={styles.primaryBtn}
            disabled={uploading}
            onClick={() => fileInputRef.current?.click()}
          >
            {uploading ? 'Uploading…' : 'Upload file'}
          </button>
          <p className={styles.placeholderText} style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
            Allowed: pdf, png, jpg, jpeg, doc, docx, xls, xlsx, csv. Max {MAX_SIZE_MB} MB.
          </p>
        </div>
      )}
    </div>
  )
}
