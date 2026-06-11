/** Resolve API URLs — same-origin via nginx (:3000) or direct backend (:8000). */

export function clientHost(): string {
  return window.location.hostname || 'localhost'
}

/** Same-origin API (nginx proxies /api → backend). Use for camera publisher uploads. */
export function publishApiBase(): string {
  return '/api/v1'
}

/** Direct backend URL (debug / WebRTC discovery only). */
export function backendBase(): string {
  const host = clientHost()
  const protocol = window.location.protocol === 'https:' ? 'https' : 'http'
  return `${protocol}://${host}:8000`
}

export function apiBase(): string {
  return `${backendBase()}/api/v1`
}

export function wsBase(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${protocol}://${clientHost()}:8000`
}

export function frontendPort(): string {
  return window.location.port || '3000'
}

/** Build frontend URL for publisher page (phone must open this). */
export function frontendBase(lanIp?: string): string {
  const port = frontendPort()
  const host = clientHost()
  if ((host === 'localhost' || host === '127.0.0.1') && lanIp) {
    return `http://${lanIp}:${port}`
  }
  return `${window.location.protocol}//${host}:${port}`
}

export function isDockerInternalIp(ip: string): boolean {
  if (ip.startsWith('172.')) {
    const second = parseInt(ip.split('.')[1] || '0', 10)
    return second >= 16 && second <= 31
  }
  return ip.startsWith('127.') || ip === '0.0.0.0'
}

export function isApipaIp(ip: string): boolean {
  return ip.startsWith('169.254.')
}

export function isUsableLanIp(ip: string): boolean {
  return !isDockerInternalIp(ip) && !isApipaIp(ip) && ip !== '0.0.0.0'
}

export function pickLanIp(candidates: string[]): string | undefined {
  for (const raw of candidates) {
    const ip = raw.replace(/^https?:\/\//, '').split(':')[0]
    if (ip.startsWith('192.168.') && isUsableLanIp(ip)) return ip
  }
  for (const raw of candidates) {
    const ip = raw.replace(/^https?:\/\//, '').split(':')[0]
    if (ip.startsWith('10.') && isUsableLanIp(ip)) return ip
  }
  return undefined
}
