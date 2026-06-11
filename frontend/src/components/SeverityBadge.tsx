import clsx from 'clsx'

export default function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border',
        `severity-${severity}`,
      )}
    >
      {severity}
    </span>
  )
}
