import { useEffect, useRef, useState, useCallback } from 'react'

interface WSMessage {
  type: string
  data: Record<string, unknown>
}

export function useWebSocket(url: string) {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null)
  const [alerts, setAlerts] = useState<WSMessage[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const ws = new WebSocket(`${protocol}//${host}${url}`)

    ws.onopen = () => setConnected(true)
    ws.onclose = () => {
      setConnected(false)
      setTimeout(connect, 3000)
    }
    ws.onmessage = (e) => {
      const msg: WSMessage = JSON.parse(e.data)
      setLastMessage(msg)
      if (msg.type === 'alert' || msg.type === 'alarm') {
        setAlerts((prev) => [msg, ...prev].slice(0, 50))
      }
    }
    wsRef.current = ws
  }, [url])

  useEffect(() => {
    connect()
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 30000)
    return () => {
      clearInterval(interval)
      wsRef.current?.close()
    }
  }, [connect])

  return { connected, lastMessage, alerts, clearAlerts: () => setAlerts([]) }
}
