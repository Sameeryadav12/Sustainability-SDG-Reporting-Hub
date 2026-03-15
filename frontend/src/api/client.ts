/**
 * Central API client. Base URL from env; attaches Bearer token when present.
 */

export const getBaseUrl = (): string => {
  const url = import.meta.env.VITE_API_BASE_URL
  if (!url || typeof url !== 'string') {
    return 'http://localhost:8000/api/v1'
  }
  return url.replace(/\/$/, '')
}

const getToken = (): string | null => {
  return localStorage.getItem('access_token')
}

export type ApiError = {
  message: string
  status: number
  detail?: string
}

/** Turn API error detail (string, array of validation errors, or object) into a single readable string. */
function detailToString(detail: unknown): string {
  if (detail == null) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item: unknown) => {
        if (item && typeof item === 'object' && 'msg' in item) return String((item as { msg: unknown }).msg)
        return JSON.stringify(item)
      })
      .filter(Boolean)
      .join('. ') || ''
  }
  if (typeof detail === 'object') {
    const d = detail as Record<string, unknown>
    if ('msg' in d && typeof d.msg === 'string') return d.msg
    if ('message' in d && typeof d.message === 'string') return d.message
    return JSON.stringify(detail)
  }
  return String(detail)
}

async function handleResponse<T>(res: Response): Promise<T> {
  const text = await res.text()
  let data: unknown
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = null
  }

  if (!res.ok) {
    const rawDetail =
      typeof data === 'object' && data !== null && 'detail' in data
        ? (data as { detail: unknown }).detail
        : res.statusText
    const detail = detailToString(rawDetail)
    const is503NotConfigured =
      res.status === 503 &&
      detail &&
      (detail.toLowerCase().includes('not configured') || detail.toLowerCase().includes('openai_api_key'))
    // Only show "Unable to connect" for real network failure (status 0). For 5xx always show server error + detail.
    const message =
      res.status === 401
        ? 'Your session has expired. Please log in again.'
        : res.status === 0
          ? 'Unable to connect to the server. Check that the backend is running and the URL is correct.'
          : is503NotConfigured
            ? detail || 'AI generation is not configured.'
            : res.status >= 500
              ? `Server error: ${detail || res.statusText || 'Please try again.'}`
              : detail || 'Something went wrong.'
    const err: ApiError = { message, status: res.status, detail: detail || undefined }
    throw err
  }

  return data as T
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const base = getBaseUrl()
  const url = path.startsWith('http') ? path : `${base}${path.startsWith('/') ? '' : '/'}${path}`
  const token = getToken()
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }
  let res: Response
  try {
    res = await fetch(url, { ...options, headers })
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Unable to connect to the server.'
    const outMsg = msg.includes('fetch') ? 'Unable to connect to the server.' : msg
    throw { message: outMsg, status: 0, detail: undefined } as ApiError
  }
  return handleResponse<T>(res)
}

export function getApiBaseUrl(): string {
  return getBaseUrl()
}

/**
 * Upload a file (multipart/form-data). Use for evidence upload. Do not set Content-Type.
 */
export async function apiUploadFile<T>(
  path: string,
  formData: FormData,
  method: 'POST' = 'POST'
): Promise<T> {
  const base = getBaseUrl()
  const url = path.startsWith('http') ? path : `${base}${path.startsWith('/') ? '' : '/'}${path}`
  const token = getToken()
  const headers: HeadersInit = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
  let res: Response
  try {
    res = await fetch(url, { method, headers, body: formData })
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Unable to connect to the server.'
    throw { message: msg.includes('fetch') ? 'Unable to connect to the server.' : msg, status: 0, detail: undefined } as ApiError
  }
  return handleResponse<T>(res)
}

/**
 * Download a file (e.g. CSV) with auth. Triggers browser download.
 */
export async function downloadFile(path: string, defaultFilename: string): Promise<void> {
  const base = getBaseUrl()
  const url = path.startsWith('http') ? path : `${base}${path.startsWith('/') ? '' : '/'}${path}`
  const token = getToken()
  const headers: HeadersInit = {}
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }
  let res: Response
  try {
    res = await fetch(url, { headers })
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Unable to connect to the server.'
    throw { message: msg.includes('fetch') ? 'Unable to connect to the server.' : msg, status: 0 } as ApiError
  }
  if (!res.ok) {
    const text = await res.text()
    let detail = res.statusText
    try {
      const data = text ? JSON.parse(text) : null
      if (data && typeof data === 'object' && data.detail) detail = String(data.detail)
    } catch {
      detail = text || detail
    }
    throw { message: detail || 'Download failed.', status: res.status } as ApiError
  }
  const cd = res.headers.get('Content-Disposition')
  let filename = defaultFilename
  const match = cd?.match(/filename="?([^";\n]+)"?/)
  if (match?.[1]) filename = match[1].trim()
  const blob = await res.blob()
  const blobUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = filename
  a.click()
  URL.revokeObjectURL(blobUrl)
}
