/**
 * RAG Status Badge component
 * Displays Green, Amber, or Red status
 */
import { clsx } from 'clsx'

type RAGStatus = 'Green' | 'Amber' | 'Red'

interface RAGBadgeProps {
  status: RAGStatus
  className?: string
}

export function RAGBadge({ status, className }: RAGBadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        {
          'bg-green-100 text-green-800': status === 'Green',
          'bg-amber-100 text-amber-800': status === 'Amber',
          'bg-red-100 text-red-800': status === 'Red',
        },
        className
      )}
    >
      {status}
    </span>
  )
}

