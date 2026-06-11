import { useCallback, useEffect, useState } from 'react'

import { motion, AnimatePresence } from 'framer-motion'

import { Scan, Play, HelpCircle, CheckCircle2, Loader2, AlertCircle } from 'lucide-react'

import { api, type Room, type Camera, type LearningResult } from '../lib/api'

import CameraSourcePicker, { type CameraSourceType } from '../components/CameraSourcePicker'

import PublishLinkCard from '../components/PublishLinkCard'



export default function Configure() {

  const [rooms, setRooms] = useState<Room[]>([])

  const [cameras, setCameras] = useState<Camera[]>([])

  const [selectedRoom, setSelectedRoom] = useState('')

  const [selectedCamera, setSelectedCamera] = useState('')

  const [newRoomName, setNewRoomName] = useState('')

  const [newCamName, setNewCamName] = useState('')

  const [sourceType, setSourceType] = useState<CameraSourceType>('webcam')

  const [streamUrl, setStreamUrl] = useState('rtsp://camera.local/stream')

  const [lastCreatedCamera, setLastCreatedCamera] = useState<Camera | null>(null)

  const [learning, setLearning] = useState(false)

  const [learningResult, setLearningResult] = useState<LearningResult | null>(null)

  const [learningError, setLearningError] = useState('')

  const [learningSuccess, setLearningSuccess] = useState('')

  const [labeling, setLabeling] = useState<string | null>(null)

  const [labelName, setLabelName] = useState('')

  const [phase, setPhase] = useState<1 | 2 | 3>(1)

  const [surveillanceActive, setSurveillanceActive] = useState(false)

  const [surveillanceError, setSurveillanceError] = useState('')

  const [surveillanceSuccess, setSurveillanceSuccess] = useState('')

  const [surveillanceLoading, setSurveillanceLoading] = useState(false)



  const load = useCallback(() => {

    api.getRooms().then(setRooms).catch(console.error)

    api.getCameras().then(setCameras).catch(console.error)

  }, [])



  useEffect(() => { load() }, [load])



  useEffect(() => {

    const interval = setInterval(() => api.getCameras().then(setCameras).catch(console.error), 3000)

    return () => clearInterval(interval)

  }, [])



  useEffect(() => {

    if (!selectedCamera) return

    const cam = cameras.find((c) => c.id === selectedCamera)

    if (cam?.room_id) setSelectedRoom(cam.room_id)

  }, [selectedCamera, cameras])



  useEffect(() => {

    if (!selectedRoom) return

    const room = rooms.find((r) => r.id === selectedRoom)

    if (room?.baseline_learned) setPhase((p) => (p < 2 ? 2 : p))



    api.getSurveillanceStatus(selectedRoom)

      .then((st) => {

        setSurveillanceActive(st.active)

        if (st.active) setPhase(3)

      })

      .catch(() => {})

  }, [selectedRoom, rooms])



  const createRoom = async () => {

    if (!newRoomName) return

    await api.createRoom({ name: newRoomName })

    setNewRoomName('')

    load()

  }



  const createCamera = async () => {

    if (!selectedRoom || !newCamName) return

    const cam = await api.createCamera({

      room_id: selectedRoom,

      name: newCamName,

      source_type: sourceType,

      stream_url: sourceType === 'rtsp' ? streamUrl : '',

    })

    setLastCreatedCamera(cam)

    setNewCamName('')

    setSelectedCamera(cam.id)

    load()

  }



  const startLearning = async () => {

    if (!selectedCamera) return

    setLearning(true)

    setLearningError('')

    setLearningSuccess('')

    try {

      const result = await api.startLearning(selectedCamera)

      setLearningResult(result)

      setLearningSuccess(result.message || `Detected ${result.objects_detected} object(s).`)

      setPhase(2)

      load()

    } catch (e) {

      setLearningResult(null)

      setLearningError(e instanceof Error ? e.message : 'Learning failed')

    } finally {

      setLearning(false)

    }

  }



  const labelObject = async (objectId: string) => {

    if (!labelName) return

    await api.labelObject(objectId, { name: labelName, category: 'general' })

    setLabeling(null)

    setLabelName('')

    if (learningResult) {

      setLearningResult({

        ...learningResult,

        unknown_objects: learningResult.unknown_objects.filter((o) => o.object_id !== objectId),

      })

    }

    setLearningSuccess(`Labeled "${labelName}". Remaining unknowns shown below.`)

  }



  const startSurveillance = async () => {

    const roomId = selectedRoom || cameras.find((c) => c.id === selectedCamera)?.room_id

    if (!roomId) {

      setSurveillanceError('Select a room or camera first.')

      return

    }

    setSurveillanceLoading(true)

    setSurveillanceError('')

    setSurveillanceSuccess('')

    try {

      const result = await api.startSurveillance(roomId)

      setSurveillanceActive(true)

      setSurveillanceSuccess(result.message || 'Surveillance is now active.')

      setPhase(3)

      if (!selectedRoom) setSelectedRoom(roomId)

    } catch (e) {

      setSurveillanceError(e instanceof Error ? e.message : 'Failed to start surveillance')

    } finally {

      setSurveillanceLoading(false)

    }

  }



  const selectedCamObj = cameras.find((c) => c.id === selectedCamera) || lastCreatedCamera

  const browserCameras = cameras.filter((c) => c.source_type === 'webcam' || c.source_type === 'mobile')

  const activeRoom = rooms.find((r) => r.id === selectedRoom)



  const phases = [

    { num: 1, title: 'Environment Learning', desc: 'AI scans and inventories all visible objects' },

    { num: 2, title: 'Identity & Labeling', desc: 'Label unknown objects and register persons' },

    { num: 3, title: 'Surveillance Active', desc: 'Continuous monitoring and threat detection' },

  ]



  return (

    <div className="p-6 space-y-6 max-w-5xl">

      <div>

        <h2 className="text-2xl font-bold tracking-tight">System Configuration</h2>

        <p className="text-gray-400 text-sm mt-1">Use laptop webcam or mobile camera for demos — no CCTV required</p>

      </div>



      <div className="flex gap-4">

        {phases.map((p) => (

          <div

            key={p.num}

            className={`flex-1 glass-card p-4 border-2 transition-colors ${

              phase === p.num ? 'border-sentinel-500/50' : phase > p.num ? 'border-green-500/30' : 'border-transparent'

            }`}

          >

            <div className="flex items-center gap-2 mb-2">

              <span className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold ${

                phase > p.num ? 'bg-green-500/20 text-green-400' : phase === p.num ? 'bg-sentinel-500/20 text-sentinel-400' : 'bg-gray-700 text-gray-400'

              }`}>

                {phase > p.num ? <CheckCircle2 className="w-4 h-4" /> : p.num}

              </span>

              <h3 className="font-semibold text-sm">{p.title}</h3>

            </div>

            <p className="text-xs text-gray-500">{p.desc}</p>

          </div>

        ))}

      </div>



      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <motion.div className="glass-card p-5 space-y-4">

          <h3 className="font-semibold flex items-center gap-2">

            <Scan className="w-4 h-4 text-sentinel-400" /> Room & Camera Setup

          </h3>



          <div className="flex gap-2">

            <input className="input-field flex-1" placeholder="Room name (e.g. Office-01)" value={newRoomName} onChange={(e) => setNewRoomName(e.target.value)} />

            <button onClick={createRoom} className="btn-primary">Add Room</button>

          </div>



          <select className="input-field" value={selectedRoom} onChange={(e) => setSelectedRoom(e.target.value)}>

            <option value="">Select room...</option>

            {rooms.map((r) => (

              <option key={r.id} value={r.id}>{r.name} {r.baseline_learned ? '✓ learned' : ''}</option>

            ))}

          </select>



          <div>

            <p className="text-xs text-gray-400 mb-2">Camera source</p>

            <CameraSourcePicker value={sourceType} onChange={setSourceType} />

          </div>



          <input className="input-field" placeholder="Camera name" value={newCamName} onChange={(e) => setNewCamName(e.target.value)} />



          {sourceType === 'rtsp' && (

            <input className="input-field" placeholder="rtsp://192.168.1.100/stream" value={streamUrl} onChange={(e) => setStreamUrl(e.target.value)} />

          )}



          <button onClick={createCamera} className="btn-primary w-full" disabled={!selectedRoom}>

            Add {sourceType === 'rtsp' ? 'CCTV' : sourceType === 'webcam' ? 'Webcam' : 'Mobile'} Camera

          </button>



          {(lastCreatedCamera || selectedCamObj) &&

            (lastCreatedCamera?.source_type !== 'rtsp' || selectedCamObj?.source_type !== 'rtsp') && (

            <PublishLinkCard camera={(selectedCamObj?.publish_url ? selectedCamObj : lastCreatedCamera)!} />

          )}



          <select className="input-field" value={selectedCamera} onChange={(e) => setSelectedCamera(e.target.value)}>

            <option value="">Select camera for learning...</option>

            {cameras.map((c) => (

              <option key={c.id} value={c.id}>

                {c.name} ({c.source_type}) {c.is_streaming ? '● live' : ''}

              </option>

            ))}

          </select>



          {selectedCamObj && selectedCamObj.source_type !== 'rtsp' && (

            <PublishLinkCard camera={selectedCamObj} />

          )}



          {learningError && (

            <div className="p-3 rounded-lg bg-threat-critical/10 border border-threat-critical/30 text-threat-critical text-sm flex gap-2">

              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />

              <span>{learningError}</span>

            </div>

          )}



          {learningSuccess && (

            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 text-sm flex gap-2">

              <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />

              <span>{learningSuccess}</span>

            </div>

          )}



          <button onClick={startLearning} disabled={!selectedCamera || learning} className="btn-primary w-full flex items-center justify-center gap-2">

            {learning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Scan className="w-4 h-4" />}

            {learning ? 'Scanning Environment...' : activeRoom?.baseline_learned ? 'Rescan Environment' : 'Start Environment Learning'}

          </button>



          {selectedCamObj?.source_type !== 'rtsp' && !selectedCamObj?.is_streaming && (

            <p className="text-xs text-threat-medium">

              Start the camera publisher first (link above), then run environment learning.

            </p>

          )}



          {activeRoom?.baseline_learned && (

            <p className="text-xs text-gray-500">

              Room already has a baseline. Rescanning will not duplicate known assets — only new or uncertain objects are added.

            </p>

          )}

        </motion.div>



        <motion.div className="glass-card p-5 space-y-4">

          <h3 className="font-semibold flex items-center gap-2">

            <HelpCircle className="w-4 h-4 text-threat-medium" /> Unknown Objects

          </h3>



          {browserCameras.length > 0 && !learningResult && (

            <div className="p-3 rounded-lg bg-sentinel-500/5 border border-sentinel-500/20 text-xs text-gray-400">

              <strong className="text-sentinel-300">Demo tip:</strong> Point your {browserCameras.map((c) => c.source_type).join(' or ')} camera at your desk setup, then run learning to detect real objects in view.

            </div>

          )}



          <AnimatePresence>

            {learningResult?.unknown_objects?.length ? (

              learningResult.unknown_objects.map((obj) => (

                <motion.div

                  key={obj.object_id}

                  initial={{ opacity: 0, y: 10 }}

                  animate={{ opacity: 1, y: 0 }}

                  className="p-3 rounded-lg bg-surface-elevated border border-threat-medium/20"

                >

                  <p className="text-sm font-medium">{obj.message}</p>

                  <p className="text-xs text-gray-500 mt-1">Confidence: {obj.confidence}%</p>

                  {labeling === obj.object_id ? (

                    <div className="flex gap-2 mt-2">

                      <input className="input-field flex-1" placeholder="Object name" value={labelName} onChange={(e) => setLabelName(e.target.value)} />

                      <button onClick={() => labelObject(obj.object_id)} className="btn-primary text-sm">Save</button>

                    </div>

                  ) : (

                    <button onClick={() => setLabeling(obj.object_id)} className="btn-ghost text-sm mt-2 text-sentinel-400">

                      Label this object →

                    </button>

                  )}

                </motion.div>

              ))

            ) : (

              <p className="text-gray-500 text-sm">

                {learningResult

                  ? `✓ ${learningResult.objects_detected} scanned — ${learningResult.objects_added} added, ${learningResult.objects_skipped} already known.`

                  : 'Run environment learning to detect objects.'}

              </p>

            )}

          </AnimatePresence>



          <div className="border-t border-surface-border pt-4 space-y-3">

            {surveillanceError && (

              <div className="p-3 rounded-lg bg-threat-critical/10 border border-threat-critical/30 text-threat-critical text-sm flex gap-2">

                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />

                <span>{surveillanceError}</span>

              </div>

            )}



            {surveillanceSuccess && (

              <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 text-sm flex gap-2">

                <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />

                <span>{surveillanceSuccess}</span>

              </div>

            )}



            <button

              onClick={startSurveillance}

              disabled={surveillanceLoading || surveillanceActive || (!selectedRoom && !selectedCamera)}

              className="btn-primary w-full flex items-center justify-center gap-2 py-3"

            >

              {surveillanceLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}

              {surveillanceActive ? 'Surveillance Active' : surveillanceLoading ? 'Starting...' : 'Activate Surveillance'}

            </button>



            {!activeRoom?.baseline_learned && (

              <p className="text-xs text-threat-medium">Complete environment learning before activating surveillance.</p>

            )}



            {surveillanceActive && (

              <p className="text-xs text-gray-500">Monitoring is running. Check Events and Threat Center for live alerts.</p>

            )}

          </div>

        </motion.div>

      </div>

    </div>

  )

}


