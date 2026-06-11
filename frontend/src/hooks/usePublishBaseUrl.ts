import { useCallback, useEffect, useState } from 'react'

import { frontendPort, isUsableLanIp, pickLanIp } from '../lib/urls'



const STORAGE_KEY = 'sentinel_publish_lan_base'



async function discoverLocalIps(): Promise<string[]> {

  const found = new Set<string>()

  return new Promise((resolve) => {

    try {

      const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] })

      pc.createDataChannel('sentinel')

      pc.onicecandidate = (event) => {

        if (!event.candidate?.candidate) return

        const match = event.candidate.candidate.match(/(\d+\.\d+\.\d+\.\d+)/)

        if (match && isUsableLanIp(match[1])) {

          found.add(match[1])

        }

      }

      pc.createOffer().then((offer) => pc.setLocalDescription(offer)).catch(() => {})

      setTimeout(() => {

        pc.close()

        resolve([...found])

      }, 2500)

    } catch {

      resolve([])

    }

  })

}



/** LAN base URL for mobile QR links. Webcam links always use window.location.origin on this machine. */

export function usePublishBaseUrl(forMobile = false) {

  const [lanBaseUrl, setLanBaseUrlState] = useState(() =>

    forMobile ? localStorage.getItem(STORAGE_KEY) || '' : '',

  )

  const [lanIp, setLanIp] = useState<string | undefined>()

  const [candidates, setCandidates] = useState<string[]>([])

  const [warning, setWarning] = useState<string | null>(null)

  const [loading, setLoading] = useState(forMobile)



  const refresh = useCallback(async () => {

    if (!forMobile) return

    setLoading(true)

    const port = frontendPort()

    const urls = new Set<string>()

    let netWarning: string | null = null



    try {

      const res = await fetch('/api/v1/system/network-hints')

      if (res.ok) {

        const data = await res.json()

        netWarning = data.warning || null

        for (const c of data.candidates || []) {

          if (!c.includes('172.') && !c.includes('169.254.')) urls.add(c)

        }

        if (data.recommended_base_url && !data.recommended_base_url.includes('172.')) {

          urls.add(data.recommended_base_url)

        }

      }

    } catch {

      /* ignore */

    }



    const localIps = await discoverLocalIps()

    for (const ip of localIps) {

      if (isUsableLanIp(ip)) urls.add(`http://${ip}:${port}`)

    }



    const sorted = [...urls].filter((u) => !u.includes('172.') && !u.includes('169.254.')).sort((a, b) => {

      const score = (u: string) => {

        if (u.includes('192.168.')) return 0

        if (u.includes('10.')) return 1

        if (u.includes('localhost') || u.includes('127.0.0.1')) return 3

        return 2

      }

      return score(a) - score(b)

    })



    setCandidates(sorted)

    setWarning(netWarning)



    const discovered = pickLanIp(sorted) || pickLanIp(localIps)

    setLanIp(discovered)



    const stored = localStorage.getItem(STORAGE_KEY)

    const storedValid = stored && !stored.includes('localhost') && !stored.includes('169.254.')



    if (storedValid) {

      setLanBaseUrlState(stored)

    } else if (discovered) {

      const url = `http://${discovered}:${port}`

      setLanBaseUrlState(url)

      localStorage.setItem(STORAGE_KEY, url)

    } else if (sorted[0] && !sorted[0].includes('localhost')) {

      setLanBaseUrlState(sorted[0])

    } else {

      setLanBaseUrlState('')

    }



    setLoading(false)

  }, [forMobile])



  useEffect(() => {

    refresh()

  }, [refresh])



  const setLanBaseUrl = (url: string) => {

    setLanBaseUrlState(url)

    localStorage.setItem(STORAGE_KEY, url)

  }



  const setManualIp = (ip: string) => {

    const trimmed = ip.trim().replace(/^https?:\/\//, '').split(':')[0]

    if (!trimmed) return

    const url = `http://${trimmed}:${frontendPort()}`

    setLanBaseUrl(url)

    setLanIp(trimmed)

  }



  const buildPublishUrl = (publishPath: string) => {

    const path = publishPath.startsWith('/') ? publishPath : `/${publishPath}`

    if (!forMobile) {

      return `${window.location.origin}${path}`

    }

    const base = lanBaseUrl || (lanIp ? `http://${lanIp}:${frontendPort()}` : '')

    if (!base) return path

    return `${base.replace(/\/$/, '')}${path}`

  }



  return {

    baseUrl: forMobile ? lanBaseUrl : window.location.origin,

    setBaseUrl: setLanBaseUrl,

    setManualIp,

    candidates,

    lanIp,

    warning,

    loading,

    refresh,

    buildPublishUrl,

  }

}


