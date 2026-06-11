import { useEffect, useState } from 'react'
import { api, type Room, type Camera, type Person, type AlertRule, type EnvObject } from '../lib/api'
import EntityActions from '../components/EntityActions'
import ConfirmDialog from '../components/ConfirmDialog'
type Tab = 'rooms' | 'cameras' | 'persons' | 'alerts' | 'assets'

export default function Manage() {
  const [tab, setTab] = useState<Tab>('cameras')
  const [rooms, setRooms] = useState<Room[]>([])
  const [cameras, setCameras] = useState<Camera[]>([])
  const [persons, setPersons] = useState<Person[]>([])
  const [alerts, setAlerts] = useState<AlertRule[]>([])
  const [objects, setObjects] = useState<EnvObject[]>([])
  const [selectedRoom, setSelectedRoom] = useState('')
  const [confirm, setConfirm] = useState<{ title: string; message: string; onOk: () => void } | null>(null)
  const [editing, setEditing] = useState<Record<string, string>>({})

  const load = () => {
    api.getRooms().then(setRooms).catch(console.error)
    api.getCameras().then(setCameras).catch(console.error)
    api.getPersons().then(setPersons).catch(console.error)
    api.getAlertRules().then(setAlerts).catch(console.error)
    if (selectedRoom) api.getObjects(selectedRoom).then(setObjects).catch(console.error)
  }

  useEffect(() => { load() }, [])
  useEffect(() => {
    if (selectedRoom) api.getObjects(selectedRoom).then(setObjects).catch(console.error)
    else setObjects([])
  }, [selectedRoom])
  useEffect(() => {
    if (rooms.length && !selectedRoom) setSelectedRoom(rooms[0].id)
  }, [rooms, selectedRoom])

  const tabs: { id: Tab; label: string }[] = [
    { id: 'rooms', label: 'Rooms' },
    { id: 'cameras', label: 'Cameras' },
    { id: 'persons', label: 'Persons' },
    { id: 'alerts', label: 'Alerts' },
    { id: 'assets', label: 'Assets' },
  ]

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Resource Management</h2>
        <p className="text-gray-400 text-sm mt-1">Add, edit, and remove rooms, cameras, persons, alerts, and assets</p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t.id ? 'bg-sentinel-600/20 text-sentinel-300 border border-sentinel-500/30' : 'text-gray-400 hover:bg-white/5'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'rooms' && (
        <div className="glass-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-surface-border text-gray-400">
              <tr>
                <th className="text-left p-4">Name</th>
                <th className="text-left p-4">Cameras</th>
                <th className="text-left p-4">Objects</th>
                <th className="text-right p-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rooms.map((r) => (
                <tr key={r.id} className="border-b border-surface-border/50 hover:bg-white/[0.02]">
                  <td className="p-4">
                    {editing[`room-${r.id}`] !== undefined ? (
                      <input className="input-field" value={editing[`room-${r.id}`]} onChange={(e) => setEditing({ ...editing, [`room-${r.id}`]: e.target.value })} />
                    ) : (
                      <span className="font-medium">{r.name}</span>
                    )}
                  </td>
                  <td className="p-4 text-gray-400">{r.camera_count}</td>
                  <td className="p-4 text-gray-400">{r.object_count}</td>
                  <td className="p-4 flex justify-end gap-2">
                    {editing[`room-${r.id}`] !== undefined ? (
                      <>
                        <button type="button" className="btn-primary text-xs" onClick={async () => {
                          await api.updateRoom(r.id, { name: editing[`room-${r.id}`] })
                          setEditing((e) => { const n = { ...e }; delete n[`room-${r.id}`]; return n })
                          load()
                        }}>Save</button>
                        <button type="button" className="btn-ghost text-xs" onClick={() => setEditing((e) => { const n = { ...e }; delete n[`room-${r.id}`]; return n })}>Cancel</button>
                      </>
                    ) : (
                      <EntityActions
                        onEdit={() => setEditing({ ...editing, [`room-${r.id}`]: r.name })}
                        onDelete={() => setConfirm({
                          title: 'Delete room?',
                          message: `Remove "${r.name}" and all its cameras and objects.`,
                          onOk: async () => { await api.deleteRoom(r.id); setConfirm(null); load() },
                        })}
                      />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'cameras' && (
        <div className="space-y-3">
          {cameras.map((c) => (
            <div key={c.id} className="glass-card p-4 flex items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                {editing[`cam-${c.id}-name`] !== undefined ? (
                  <div className="space-y-2">
                    <input className="input-field" placeholder="Name" value={editing[`cam-${c.id}-name`]} onChange={(e) => setEditing({ ...editing, [`cam-${c.id}-name`]: e.target.value })} />
                    {c.source_type === 'rtsp' && (
                      <input className="input-field" placeholder="Stream URL" value={editing[`cam-${c.id}-url`] || c.stream_url} onChange={(e) => setEditing({ ...editing, [`cam-${c.id}-url`]: e.target.value })} />
                    )}
                  </div>
                ) : (
                  <>
                    <p className="font-medium">{c.name} <span className="text-xs text-gray-500">({c.source_type})</span></p>
                    <p className="text-xs text-gray-500 truncate">{c.source_type === 'rtsp' ? c.stream_url : c.publish_path}</p>
                  </>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">{c.status}</span>
                {editing[`cam-${c.id}-name`] !== undefined ? (
                  <>
                    <button type="button" className="btn-primary text-xs" onClick={async () => {
                      await api.updateCamera(c.id, {
                        name: editing[`cam-${c.id}-name`],
                        ...(editing[`cam-${c.id}-url`] ? { stream_url: editing[`cam-${c.id}-url`] } : {}),
                      })
                      setEditing((e) => { const n = { ...e }; delete n[`cam-${c.id}-name`]; delete n[`cam-${c.id}-url`]; return n })
                      load()
                    }}>Save</button>
                    <button type="button" className="btn-ghost text-xs" onClick={() => setEditing((e) => { const n = { ...e }; delete n[`cam-${c.id}-name`]; return n })}>Cancel</button>
                  </>
                ) : (
                  <EntityActions
                    onEdit={() => setEditing({ ...editing, [`cam-${c.id}-name`]: c.name, [`cam-${c.id}-url`]: c.stream_url })}
                    onDelete={() => setConfirm({
                      title: 'Delete camera?',
                      message: `Remove "${c.name}" from the system.`,
                      onOk: async () => { await api.deleteCamera(c.id); setConfirm(null); load() },
                    })}
                  />
                )}
              </div>
            </div>
          ))}
          {!cameras.length && <p className="text-gray-500 text-center py-8">No cameras. Add one in Configure.</p>}
        </div>
      )}

      {tab === 'persons' && (
        <div className="space-y-3">
          {persons.map((p) => (
            <div key={p.id} className="glass-card p-4 flex items-center justify-between">
              <div>
                {editing[`person-${p.id}`] !== undefined ? (
                  <input className="input-field" value={editing[`person-${p.id}`]} onChange={(e) => setEditing({ ...editing, [`person-${p.id}`]: e.target.value })} />
                ) : (
                  <>
                    <p className="font-medium">{p.name}</p>
                    <p className="text-xs text-gray-500">{p.role} · {p.access_level}</p>
                  </>
                )}
              </div>
              <div className="flex gap-2">
                {editing[`person-${p.id}`] !== undefined ? (
                  <>
                    <button type="button" className="btn-primary text-xs" onClick={async () => {
                      await api.updatePerson(p.id, { name: editing[`person-${p.id}`] })
                      setEditing((e) => { const n = { ...e }; delete n[`person-${p.id}`]; return n })
                      load()
                    }}>Save</button>
                    <button type="button" className="btn-ghost text-xs" onClick={() => setEditing((e) => { const n = { ...e }; delete n[`person-${p.id}`]; return n })}>Cancel</button>
                  </>
                ) : (
                  <EntityActions
                    onEdit={() => setEditing({ ...editing, [`person-${p.id}`]: p.name })}
                    onDelete={() => setConfirm({
                      title: 'Remove person?',
                      message: `Deactivate "${p.name}" from known persons.`,
                      onOk: async () => { await api.deletePerson(p.id); setConfirm(null); load() },
                    })}
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'alerts' && (
        <div className="space-y-3">
          {alerts.map((a) => (
            <div key={a.id} className="glass-card p-4 flex items-center justify-between">
              <div>
                <p className="font-medium">{a.name}</p>
                <p className="text-xs text-gray-500">{a.event_type} · {a.min_severity} · {a.is_active ? 'active' : 'disabled'}</p>
              </div>
              <div className="flex items-center gap-2">
                <button type="button" className="btn-ghost text-xs" onClick={async () => {
                  await api.updateAlertRule(a.id, { is_active: !a.is_active })
                  load()
                }}>{a.is_active ? 'Disable' : 'Enable'}</button>
                <EntityActions
                  onDelete={() => setConfirm({
                    title: 'Delete alert rule?',
                    message: `Remove "${a.name}".`,
                    onOk: async () => { await api.deleteAlertRule(a.id); setConfirm(null); load() },
                  })}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'assets' && (
        <div className="space-y-4">
          <select className="input-field w-64" value={selectedRoom} onChange={(e) => setSelectedRoom(e.target.value)}>
            {rooms.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
          </select>
          <div className="space-y-3">
            {objects.map((o) => (
              <div key={o.id} className="glass-card p-4 flex items-center justify-between">
                <div>
                  {editing[`obj-${o.id}`] !== undefined ? (
                    <input className="input-field" value={editing[`obj-${o.id}`]} onChange={(e) => setEditing({ ...editing, [`obj-${o.id}`]: e.target.value })} />
                  ) : (
                    <>
                      <p className="font-medium">{o.name}</p>
                      <p className="text-xs text-gray-500">{o.category} · {o.state}</p>
                    </>
                  )}
                </div>
                <div className="flex gap-2">
                  {editing[`obj-${o.id}`] !== undefined ? (
                    <>
                      <button type="button" className="btn-primary text-xs" onClick={async () => {
                        await api.updateObject(o.id, { name: editing[`obj-${o.id}`] })
                        setEditing((e) => { const n = { ...e }; delete n[`obj-${o.id}`]; return n })
                        load()
                      }}>Save</button>
                      <button type="button" className="btn-ghost text-xs" onClick={() => setEditing((e) => { const n = { ...e }; delete n[`obj-${o.id}`]; return n })}>Cancel</button>
                    </>
                  ) : (
                    <EntityActions
                      onEdit={() => setEditing({ ...editing, [`obj-${o.id}`]: o.name })}
                      onDelete={() => setConfirm({
                        title: 'Delete asset?',
                        message: `Remove "${o.name}" from inventory.`,
                        onOk: async () => { await api.deleteObject(o.id); setConfirm(null); load() },
                      })}
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <ConfirmDialog
        open={!!confirm}
        title={confirm?.title || ''}
        message={confirm?.message || ''}
        onConfirm={() => confirm?.onOk()}
        onCancel={() => setConfirm(null)}
      />
    </div>
  )
}
