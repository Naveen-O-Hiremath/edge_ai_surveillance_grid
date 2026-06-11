import { useEffect, useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { UserPlus, Camera, CheckCircle2 } from 'lucide-react'
import { api, type Person } from '../lib/api'

const ANGLES = ['front', 'left', 'right', 'up', 'down'] as const

export default function Persons() {
  const [persons, setPersons] = useState<Person[]>([])
  const [showRegister, setShowRegister] = useState(false)
  const [name, setName] = useState('')
  const [role, setRole] = useState('employee')
  const [photos, setPhotos] = useState<Record<string, File | null>>({})
  const [registering, setRegistering] = useState(false)
  const [success, setSuccess] = useState(false)
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({})

  useEffect(() => {
    api.getPersons().then(setPersons).catch(console.error)
  }, [])

  const handlePhoto = (angle: string, file: File | null) => {
    setPhotos((prev) => ({ ...prev, [angle]: file }))
  }

  const register = async () => {
    if (!name || ANGLES.some((a) => !photos[a])) return
    setRegistering(true)
    const form = new FormData()
    form.append('name', name)
    form.append('role', role)
    ANGLES.forEach((a) => form.append(a, photos[a]!))
    try {
      await api.registerPerson(form)
      setSuccess(true)
      setShowRegister(false)
      setName('')
      setPhotos({})
      api.getPersons().then(setPersons)
      setTimeout(() => setSuccess(false), 3000)
    } catch (e) {
      console.error(e)
    } finally {
      setRegistering(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Known Persons</h2>
          <p className="text-gray-400 text-sm mt-1">Register authorized individuals with multi-angle face capture</p>
        </div>
        <button onClick={() => setShowRegister(!showRegister)} className="btn-primary flex items-center gap-2">
          <UserPlus className="w-4 h-4" /> Register Person
        </button>
      </div>

      {success && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> Person registered successfully with 5 face embeddings
        </motion.div>
      )}

      {showRegister && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 space-y-4">
          <h3 className="font-semibold">Identity Enrollment</h3>
          <div className="grid grid-cols-2 gap-4">
            <input className="input-field" placeholder="Full name" value={name} onChange={(e) => setName(e.target.value)} />
            <select className="input-field" value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="employee">Employee</option>
              <option value="visitor">Regular Visitor</option>
              <option value="contractor">Contractor</option>
              <option value="admin">Administrator</option>
            </select>
          </div>

          <div className="grid grid-cols-5 gap-3">
            {ANGLES.map((angle) => (
              <div key={angle} className="text-center">
                <button
                  onClick={() => fileRefs.current[angle]?.click()}
                  className={`w-full aspect-square rounded-xl border-2 border-dashed flex flex-col items-center justify-center gap-1 transition-colors ${
                    photos[angle] ? 'border-green-500/50 bg-green-500/5' : 'border-surface-border hover:border-sentinel-500/30'
                  }`}
                >
                  {photos[angle] ? (
                    <CheckCircle2 className="w-6 h-6 text-green-400" />
                  ) : (
                    <Camera className="w-6 h-6 text-gray-500" />
                  )}
                  <span className="text-xs text-gray-400 capitalize">{angle}</span>
                </button>
                <input
                  ref={(el) => { fileRefs.current[angle] = el }}
                  type="file"
                  accept="image/*"
                  capture="user"
                  className="hidden"
                  onChange={(e) => handlePhoto(angle, e.target.files?.[0] || null)}
                />
              </div>
            ))}
          </div>

          <button onClick={register} disabled={registering} className="btn-primary">
            {registering ? 'Generating Embeddings...' : 'Register & Store Embeddings'}
          </button>
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {persons.map((p) => (
          <motion.div key={p.id} className="glass-card-hover p-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-sentinel-500 to-indigo-600 flex items-center justify-center text-lg font-bold">
                {p.name.charAt(0)}
              </div>
              <div>
                <h3 className="font-semibold">{p.name}</h3>
                <p className="text-xs text-gray-400 capitalize">{p.role} · {p.access_level}</p>
              </div>
            </div>
            <div className="mt-4 flex gap-4 text-xs text-gray-500">
              <span>{p.embedding_count} embeddings</span>
              <span>{p.visit_count} visits</span>
            </div>
          </motion.div>
        ))}
        {!persons.length && (
          <p className="text-gray-500 col-span-full text-center py-12">No persons registered yet</p>
        )}
      </div>
    </div>
  )
}
