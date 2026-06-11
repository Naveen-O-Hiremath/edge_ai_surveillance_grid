import { Pencil, Trash2 } from 'lucide-react'

interface Props {
  onEdit?: () => void
  onDelete?: () => void
  deleteLabel?: string
  size?: 'sm' | 'md'
}

export default function EntityActions({ onEdit, onDelete, deleteLabel = 'Delete', size = 'sm' }: Props) {
  const btnClass = size === 'sm' ? 'p-1.5' : 'p-2'
  return (
    <div className="flex items-center gap-1">
      {onEdit && (
        <button type="button" onClick={onEdit} className={`${btnClass} rounded-lg text-gray-400 hover:text-sentinel-300 hover:bg-white/5`} title="Edit">
          <Pencil className="w-4 h-4" />
        </button>
      )}
      {onDelete && (
        <button type="button" onClick={onDelete} className={`${btnClass} rounded-lg text-gray-400 hover:text-threat-critical hover:bg-threat-critical/10`} title={deleteLabel}>
          <Trash2 className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}
