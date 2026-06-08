// API client for the Aadhya admin panel
// Dev: Vite proxy /admin → localhost:8000
// Production (Vercel): same-origin /admin → Render via vercel.json rewrite (no CORS)
const BASE_URL = import.meta.env.DEV
  ? (import.meta.env.VITE_API_URL || 'http://localhost:8000')
  : ''

let authToken: string | null = sessionStorage.getItem('aadhya_admin_token')

export function setToken(token: string) {
  authToken = token
  sessionStorage.setItem('aadhya_admin_token', token)
}

export function clearToken() {
  authToken = null
  sessionStorage.removeItem('aadhya_admin_token')
}

export function isAuthenticated(): boolean {
  return !!authToken
}

async function fetchAdmin(path: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`
  }
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  if (res.status === 401) {
    clearToken()
    window.location.href = '/krsna'
    throw new Error('Unauthorized')
  }
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const api = {
  login: async (password: string) => {
    const res = await fetch(`${BASE_URL}/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      const detail = typeof data.detail === 'string' ? data.detail : 'Invalid password'
      throw new Error(detail)
    }
    return data
  },

  dashboard: () => fetchAdmin('/admin/dashboard'),
  sessions: () => fetchAdmin('/admin/sessions'),
  session: (id: string) => fetchAdmin(`/admin/session/${id}`),
  enquiries: () => fetchAdmin('/admin/enquiries'),
  summaries: () => fetchAdmin('/admin/summaries'),
  logs: (params?: { session_id?: string; event?: string; limit?: number }) => {
    const qs = new URLSearchParams()
    if (params?.session_id) qs.set('session_id', params.session_id)
    if (params?.event) qs.set('event', params.event)
    if (params?.limit) qs.set('limit', String(params.limit))
    return fetchAdmin(`/admin/logs?${qs}`)
  },
  health: () => fetchAdmin('/admin/health'),
  attachments: (sessionId?: string) =>
    fetchAdmin(sessionId ? `/admin/session/${sessionId}/attachments` : '/admin/attachments'),

  resetSession: (id: string) =>
    fetchAdmin(`/admin/session/${id}/reset`, { method: 'POST' }),
  forceSummary: (id: string) =>
    fetchAdmin(`/admin/session/${id}/force-summary`, { method: 'POST' }),
  closeSession: (id: string) =>
    fetchAdmin(`/admin/session/${id}/close`, { method: 'POST' }),
}

export function createSSEStream(onMessage: (data: object) => void) {
  const token = authToken || sessionStorage.getItem('aadhya_admin_token')
  const qs = token ? `?token=${encodeURIComponent(token)}` : ''
  const url = `${BASE_URL}/admin/stream${qs}`
  const es = new EventSource(url)
  es.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)) } catch {}
  }
  return es
}
