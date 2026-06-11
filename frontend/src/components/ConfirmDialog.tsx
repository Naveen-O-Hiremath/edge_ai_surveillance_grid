interface Props {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmDialog({ open, title, message, confirmLabel = 'Delete', onConfirm, onCancel }: Props) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="glass-card p-6 max-w-md w-full space-y-4">
        <h3 className="font-semibold text-lg">{title}</h3>
        <p className="text-sm text-gray-400">{message}</p>
        <div className="flex gap-3 justify-end">
          <button type="button" onClick={onCancel} className="btn-ghost">Cancel</button>
          <button type="button" onClick={onConfirm} className="px-4 py-2 rounded-lg bg-threat-critical hover:bg-threat-critical/80 text-white font-medium">
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
