import { useEffect, useState } from 'react'
import { Box } from 'lucide-react'
import { api, type Room, type EnvObject } from '../lib/api'

export default function Assets() {
  const [rooms, setRooms] = useState<Room[]>([])
  const [selectedRoom, setSelectedRoom] = useState('')
  const [objects, setObjects] = useState<EnvObject[]>([])

  useEffect(() => {
    api.getRooms().then((r) => {
      setRooms(r)
      if (r.length) setSelectedRoom(r[0].id)
    })
  }, [])

  useEffect(() => {
    if (selectedRoom) api.getObjects(selectedRoom).then(setObjects).catch(console.error)
  }, [selectedRoom])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Asset Inventory</h2>
          <p className="text-gray-400 text-sm mt-1">Objects detected from your last environment learning scan (live YOLO frame analysis)</p>
        </div>
        <select className="input-field w-48" value={selectedRoom} onChange={(e) => setSelectedRoom(e.target.value)}>
          {rooms.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {objects.map((obj) => (
          <div key={obj.id} className="glass-card-hover p-5">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-sentinel-500/10">
                  <Box className="w-4 h-4 text-sentinel-400" />
                </div>
                <div>
                  <h3 className="font-medium">{obj.name}</h3>
                  <p className="text-xs text-gray-500">{obj.category} · {obj.label}</p>
                </div>
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">{obj.state}</span>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
              <span>Confidence: {obj.confidence}%</span>
              {obj.admin_labeled && <span className="text-sentinel-400">Admin labeled</span>}
            </div>
          </div>
        ))}
        {!objects.length && (
          <p className="text-gray-500 col-span-full text-center py-12">
            No assets learned yet. Run environment learning in Configure with a clear camera view.
          </p>
        )}
      </div>
    </div>
  )
}
