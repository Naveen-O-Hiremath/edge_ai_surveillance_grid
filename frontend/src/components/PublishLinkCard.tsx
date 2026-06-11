import { Copy, ExternalLink, QrCode, RefreshCw, AlertTriangle } from 'lucide-react'

import { useState } from 'react'

import { QRCodeSVG } from 'qrcode.react'

import type { Camera } from '../lib/api'

import { usePublishBaseUrl } from '../hooks/usePublishBaseUrl'



interface Props {

  camera: Camera

}



export default function PublishLinkCard({ camera }: Props) {

  const [copied, setCopied] = useState(false)

  const [manualIp, setManualIp] = useState('')

  const isMobile = camera.source_type === 'mobile'

  const { baseUrl, setBaseUrl, setManualIp: applyManualIp, candidates, lanIp, warning, loading, refresh, buildPublishUrl } =

    usePublishBaseUrl(isMobile)



  if (!camera.stream_token) return null



  const publishPath = camera.publish_path || `/publish/${camera.source_type}/${camera.stream_token}`

  const fullUrl = buildPublishUrl(publishPath)

  const qrReady = isMobile && baseUrl && !baseUrl.includes('localhost')



  const copy = async () => {

    await navigator.clipboard.writeText(fullUrl)

    setCopied(true)

    setTimeout(() => setCopied(false), 2000)

  }



  const applyIp = () => {

    if (manualIp.trim()) applyManualIp(manualIp.trim())

  }



  return (

    <div className="p-4 rounded-xl bg-surface-elevated border border-sentinel-500/20 space-y-3">

      <div className="flex items-center justify-between">

        <p className="text-sm font-medium text-sentinel-300">

          {isMobile ? 'Mobile Camera Link' : 'Webcam Publisher'}

        </p>

        <span className={`text-xs px-2 py-0.5 rounded-full ${camera.is_streaming ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-400'}`}>

          {camera.is_streaming ? 'Streaming' : 'Waiting for feed'}

        </span>

      </div>



      {isMobile && warning && (

        <div className="p-3 rounded-lg bg-threat-medium/10 border border-threat-medium/30 text-threat-medium text-xs flex gap-2">

          <AlertTriangle className="w-4 h-4 flex-shrink-0" />

          <span>{warning}</span>

        </div>

      )}



      {isMobile && (

        <>

          <div>

            <label className="text-xs text-gray-400 mb-1 block">Your PC Wi-Fi IP (for phone QR)</label>

            <div className="flex gap-2">

              <select

                className="input-field flex-1 text-sm"

                value={baseUrl}

                onChange={(e) => setBaseUrl(e.target.value)}

              >

                {candidates.length === 0 && <option value="">No IP detected — enter manually below</option>}

                {candidates.map((url) => (

                  <option key={url} value={url}>{url}</option>

                ))}

                {baseUrl && !candidates.includes(baseUrl) && <option value={baseUrl}>{baseUrl}</option>}

              </select>

              <button type="button" onClick={refresh} className="btn-ghost px-3" title="Refresh network addresses">

                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />

              </button>

            </div>

          </div>



          <div>

            <label className="text-xs text-gray-400 mb-1 block">Or enter IP manually (from ipconfig → Wi-Fi)</label>

            <div className="flex gap-2">

              <input

                className="input-field flex-1 text-sm font-mono"

                placeholder="e.g. 192.168.1.105"

                value={manualIp}

                onChange={(e) => setManualIp(e.target.value)}

                onKeyDown={(e) => e.key === 'Enter' && applyIp()}

              />

              <button type="button" onClick={applyIp} className="btn-ghost px-3 text-sm">Apply</button>

            </div>

          </div>

        </>

      )}



      {isMobile && (

        <div className="flex justify-center py-2 bg-white rounded-lg min-h-[200px] items-center">

          {qrReady ? (

            <QRCodeSVG value={fullUrl} size={180} level="M" includeMargin />

          ) : (

            <p className="text-xs text-gray-500 text-center px-4">

              Connect PC to Wi-Fi, run <code className="text-gray-700">scripts\get-lan-ip.ps1</code>, then refresh — or enter your Wi-Fi IP above.

            </p>

          )}

        </div>

      )}



      <p className="text-xs text-gray-500 break-all font-mono bg-black/20 p-2 rounded">{fullUrl}</p>



      <div className="flex gap-2">

        <button type="button" onClick={copy} className="btn-ghost flex-1 flex items-center justify-center gap-1 text-sm" disabled={!fullUrl || fullUrl.startsWith('/')}>

          <Copy className="w-3 h-3" /> {copied ? 'Copied!' : 'Copy Link'}

        </button>

        <a

          href={fullUrl.startsWith('/') ? undefined : fullUrl}

          target="_blank"

          rel="noreferrer"

          className={`btn-primary flex-1 flex items-center justify-center gap-1 text-sm ${fullUrl.startsWith('/') ? 'opacity-50 pointer-events-none' : ''}`}

        >

          <ExternalLink className="w-3 h-3" />

          {isMobile ? 'Open on Phone' : 'Open Webcam'}

        </a>

      </div>



      <div className="text-[11px] text-gray-500 space-y-1">

        <p className="flex items-start gap-1">

          <QrCode className="w-3 h-3 mt-0.5 flex-shrink-0" />

          {isMobile

            ? 'PC and phone must be on the same Wi-Fi. Use your Wi-Fi IP — not Hyper-V (vEthernet) addresses like 192.168.31.128 if that is a virtual switch.'

            : 'Opens on this laptop via localhost. Allow camera permission when prompted.'}

        </p>

        {isMobile && lanIp && (

          <p className="text-sentinel-400">Using LAN IP: {lanIp}</p>

        )}

        {isMobile && (

          <p>Setup: (1) Connect PC Wi-Fi (2) Run <code className="text-gray-400">scripts\get-lan-ip.ps1</code> (3) Run <code className="text-gray-400">scripts\open-firewall.ps1</code> as Admin</p>

        )}

      </div>

    </div>

  )

}


