const API_BASE = '/api/v1'

function getToken(): string | null {
  return localStorage.getItem('sentinel_token')
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  getSystemStatus: () => request<SystemStatus>('/system/status'),

  getDashboard: () => request<DashboardData>('/analytics/dashboard'),

  getRooms: () => request<Room[]>('/rooms'),
  createRoom: (data: { name: string; description?: string }) =>
    request<Room>('/rooms', { method: 'POST', body: JSON.stringify(data) }),
  updateRoom: (id: string, data: { name?: string; description?: string }) =>
    request<Room>(`/rooms/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteRoom: (id: string) => request<{ status: string }>(`/rooms/${id}`, { method: 'DELETE' }),

  getCameras: () => request<Camera[]>('/cameras'),
  createCamera: (data: { room_id: string; name: string; stream_url?: string; source_type?: string }) =>
    request<Camera>('/cameras', { method: 'POST', body: JSON.stringify(data) }),
  updateCamera: (id: string, data: Partial<Camera>) =>
    request<Camera>(`/cameras/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteCamera: (id: string) => request<{ status: string }>(`/cameras/${id}`, { method: 'DELETE' }),
  regenerateCameraToken: (id: string) =>
    request<{ stream_token: string }>(`/cameras/${id}/regenerate-token`, { method: 'POST' }),

  getStreamStatus: (cameraId: string) =>
    request<{ connected: boolean; frame_count: number }>(`/cameras/${cameraId}/stream-status`),

  startLearning: (camera_id: string) =>
    request<LearningResult>('/cameras/configure/learning', {
      method: 'POST',
      body: JSON.stringify({ camera_id }),
    }),

  startSurveillance: (room_id: string) =>
    request<SurveillanceStartResult>('/cameras/configure/surveillance', {
      method: 'POST',
      body: JSON.stringify({ room_id }),
    }),

  getSurveillanceStatus: (room_id: string) =>
    request<SurveillanceStatus>(`/cameras/configure/surveillance/${room_id}`),

  getObjects: (roomId: string) => request<EnvObject[]>(`/objects/room/${roomId}`),
  updateObject: (id: string, data: Partial<EnvObject>) =>
    request<EnvObject>(`/objects/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteObject: (id: string) => request<{ status: string }>(`/objects/${id}`, { method: 'DELETE' }),
  labelObject: (objectId: string, data: { name: string; category: string }) =>
    request<EnvObject>(`/objects/${objectId}/label`, {
      method: 'POST',
      body: JSON.stringify({ ...data, is_tracked: true }),
    }),

  getPersons: () => request<Person[]>('/persons'),
  updatePerson: (id: string, data: Partial<Person>) =>
    request<Person>(`/persons/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deletePerson: (id: string, hard = false) =>
    request<{ status: string }>(`/persons/${id}?hard=${hard}`, { method: 'DELETE' }),
  registerPerson: (formData: FormData) =>
    request<Person>('/persons/register', { method: 'POST', body: formData, headers: {} }),

  getEvents: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return request<Event[]>(`/events${qs}`)
  },

  getIncidents: () => request<Incident[]>('/incidents'),

  getAlertRules: () => request<AlertRule[]>('/alerts/rules'),
  createAlertRule: (data: Partial<AlertRule>) =>
    request<AlertRule>('/alerts/rules', { method: 'POST', body: JSON.stringify(data) }),
  updateAlertRule: (id: string, data: Partial<AlertRule>) =>
    request<AlertRule>(`/alerts/rules/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteAlertRule: (id: string) =>
    request<{ status: string }>(`/alerts/rules/${id}`, { method: 'DELETE' }),

  generateSummary: (room_id?: string) =>
    request<Summary>('/analytics/summary', {
      method: 'POST',
      body: JSON.stringify({ period: 'daily', room_id }),
    }),

  search: (query: string) =>
    request<{ query: string; answer: string; matching_events: Event[] }>('/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    }),
}

export interface SystemStatus {
  healthy: boolean
  edge_ai_reachable: boolean
  cameras_total: number
  cameras_streaming: number
  surveillance_sessions: number
  open_incidents: number
  message: string
}

export interface DashboardData {
  stats: {
    total_cameras: number
    online_cameras: number
    active_threats: number
    events_today: number
    unknown_visitors_today: number
    asset_alerts_today: number
    open_incidents: number
    risk_score_avg: number
  }
  timeline: { hour: number; count: number; severity_breakdown: Record<string, number> }[]
  event_distribution: Record<string, number>
  severity_distribution: Record<string, number>
  heatmap: { x: number; y: number; intensity: number }[]
  top_threats: Event[]
}

export interface Room {
  id: string
  name: string
  description: string | null
  baseline_learned: boolean
  camera_count: number
  object_count: number
}

export interface Camera {
  id: string
  room_id: string
  name: string
  stream_url: string
  source_type: 'rtsp' | 'webcam' | 'mobile'
  stream_token?: string | null
  publish_path?: string | null
  publish_url?: string | null
  is_streaming?: boolean
  status: string
  health_score: number
  last_heartbeat?: string | null
}

export interface EnvObject {
  id: string
  room_id?: string
  name: string
  label: string
  category: string
  location: Record<string, unknown>
  state: string
  confidence: number
  admin_labeled: boolean
}

export interface Person {
  id: string
  name: string
  role: string
  access_level: string
  is_active?: boolean
  visit_count: number
  embedding_count: number
}

export interface Event {
  id: string
  event_type: string
  severity: string
  confidence: number
  risk_score: number
  title: string
  description: string | null
  created_at: string
}

export interface Incident {
  id: string
  title: string
  description?: string | null
  severity: string
  risk_score: number
  status: string
  ai_summary: string | null
  started_at: string
}

export interface AlertRule {
  id: string
  name: string
  event_type: string
  min_severity: string
  channels: string[]
  sound_enabled: boolean
  is_active: boolean
}

export interface LearningResult {
  objects_detected: number
  objects_added: number
  objects_updated: number
  objects_skipped: number
  unknown_objects: { label: string; confidence: number; message: string; object_id: string }[]
  status: string
  message: string
}

export interface SurveillanceStatus {
  active: boolean
  session_id: string | null
  cameras: number
  surveilling_cameras: number
}

export interface SurveillanceStartResult {
  status: string
  message: string
  session_id?: string
  cameras: number
  edge_ai_connected?: boolean
}

export interface Summary {
  narrative: string
  stats: Record<string, unknown>
  generated_at: string
}
