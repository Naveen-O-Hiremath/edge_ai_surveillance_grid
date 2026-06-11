import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Camera, Wifi, WifiOff, Smartphone, Monitor, AlertCircle, CheckCircle2 } from 'lucide-react'
import { publishApiBase } from '../lib/urls'

type PublishMode = 'webcam' | 'mobile'

export default function PublishCamera() {
  const { mode, token } = useParams<{ mode: PublishMode; token: string }>()
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const intervalRef = useRef<number | null>(null)

  const [serverOk, setServerOk] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState('')
  const [statusMsg, setStatusMsg] = useState('')
  const [framesSent, setFramesSent] = useState(0)
  const [framesFailed, setFramesFailed] = useState(0)
  const [cameraName, setCameraName] = useState('')

  const isMobile = mode === 'mobile'
  const api = publishApiBase()

  const sendFrameHttp = useCallback(async (blob: Blob): Promise<boolean> => {
    if (!token) return false
    try {
      const res = await fetch(`${api}/publish/${token}/frame`, {
        method: 'POST',
        body: blob,
        headers: { 'Content-Type': 'image/jpeg' },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        if (framesFailed === 0) {
          setError(err.detail || `Upload failed (${res.status}). Backend: ${api}`)
        }
        return false
      }
      return true
    } catch (e) {
      if (framesFailed === 0) {
        setError(`Cannot reach server at ${window.location.origin}${api}. Is Docker running?`)
      }
      return false
    }
  }, [token, api, framesFailed])

  const captureLoop = useCallback(() => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas || video.readyState < 2) return

    const w = video.videoWidth
    const h = video.videoHeight
    if (!w || !h) return

    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0, w, h)

    canvas.toBlob(
      async (blob) => {
        if (!blob) return
        const ok = await sendFrameHttp(blob)
        if (ok) {
          setFramesSent((n) => n + 1)
          setServerOk(true)
          setError('')
        } else {
          setFramesFailed((n) => n + 1)
        }
      },
      'image/jpeg',
      0.82,
    )
  }, [sendFrameHttp])

  const startCamera = async () => {
    setError('')
    setStatusMsg('Requesting camera permission...')
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Camera API unavailable. Use Chrome/Edge on localhost or your LAN IP (not 127.0.0.1 on phone).')
      return
    }

    try {
      const constraints: MediaStreamConstraints = {
        video: isMobile
          ? { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }
          : { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      }
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream

      const video = videoRef.current
      if (!video) return

      video.srcObject = stream
      video.muted = true
      video.playsInline = true
      video.setAttribute('playsinline', 'true')

      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Camera timeout')), 15000)
        video.onloadedmetadata = () => {
          clearTimeout(timeout)
          video.play().then(resolve).catch(reject)
        }
        video.onerror = () => {
          clearTimeout(timeout)
          reject(new Error('Video error'))
        }
      })

      setStatusMsg('Camera active — uploading frames...')
      setStreaming(true)
      intervalRef.current = window.setInterval(captureLoop, 300)
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      setError(
        msg.includes('NotAllowed') || msg.includes('Permission')
          ? 'Camera blocked. Click the camera icon in the address bar and allow access.'
          : `Camera error: ${msg}`,
      )
      setStatusMsg('')
    }
  }

  const stopCamera = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    setStreaming(false)
    setStatusMsg('')
  }

  useEffect(() => {
    if (!token) return

    fetch(`${api}/publish/${token}/info`)
      .then(async (r) => {
        if (!r.ok) {
          const err = await r.json().catch(() => ({}))
          throw new Error(err.detail || `Invalid link (${r.status})`)
        }
        return r.json()
      })
      .then((d) => {
        setCameraName(d.name || '')
        setServerOk(true)
        setStatusMsg(`Connected (${window.location.origin})`)
      })
      .catch((e) => {
        setError(e.message || 'Invalid camera link — recreate the camera in Configure')
      })

    return () => stopCamera()
  }, [token, api])

  return (
    <div className="min-h-screen bg-surface flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-lg space-y-4">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-sentinel-500 to-indigo-600 mb-3">
            {isMobile ? <Smartphone className="w-7 h-7 text-white" /> : <Monitor className="w-7 h-7 text-white" />}
          </div>
          <h1 className="text-xl font-bold">Sentinel Camera Publisher</h1>
          <p className="text-sm text-gray-400 mt-1">{cameraName || (isMobile ? 'Mobile camera' : 'Laptop webcam')}</p>
        </div>

        <div className="glass-card overflow-hidden">
          <div className="relative aspect-video bg-black">
            <video ref={videoRef} className="w-full h-full object-cover mirror" playsInline muted autoPlay />
            {!streaming && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/60">
                <Camera className="w-12 h-12 text-gray-600" />
              </div>
            )}
            <div className="absolute top-3 left-3 flex items-center gap-2 px-2 py-1 rounded-full bg-black/60 text-xs">
              {serverOk && streaming ? (
                <Wifi className="w-3 h-3 text-green-400" />
              ) : (
                <WifiOff className="w-3 h-3 text-yellow-400" />
              )}
              {streaming ? 'Uploading' : serverOk ? 'Ready' : 'Connecting'}
            </div>
            {streaming && framesSent > 0 && (
              <div className="absolute top-3 right-3 px-2 py-1 rounded-full bg-green-600/90 text-xs font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> LIVE · {framesSent}
              </div>
            )}
          </div>

          <div className="p-4 space-y-3">
            {error && (
              <div className="p-3 rounded-lg bg-threat-critical/10 border border-threat-critical/30 text-threat-critical text-sm flex gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {statusMsg && !error && (
              <p className="text-xs text-sentinel-300 text-center">{statusMsg}</p>
            )}

            {!streaming ? (
              <button type="button" onClick={startCamera} className="btn-primary w-full py-3">
                {isMobile ? 'Start Mobile Camera' : 'Start Webcam'}
              </button>
            ) : (
              <button type="button" onClick={stopCamera} className="w-full py-3 rounded-lg border border-threat-critical/30 text-threat-critical">
                Stop Streaming
              </button>
            )}

            <p className="text-xs text-gray-500 text-center">
              {streaming && framesSent > 0
                ? 'Frames uploading. Go to Configure → Start Environment Learning.'
                : isMobile
                  ? 'Allow camera when prompted. Phone only needs port 3000 (same Wi‑Fi).'
                  : 'Allow camera when prompted. Use localhost link on this laptop for webcam access.'}
            </p>
          </div>
        </div>
      </div>
      <canvas ref={canvasRef} className="hidden" />
      <style>{`.mirror { transform: scaleX(-1); }`}</style>
    </div>
  )
}
