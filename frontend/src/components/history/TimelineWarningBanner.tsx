/* TimelineWarningBanner — shown above the chart in Overall mode when the
   backend has flagged ratio drift. Renders the first non-null warning verbatim
   (it already contains the numeric ratios_sum value). */

interface Props {
  message: string | null
}

export function TimelineWarningBanner({ message }: Props) {
  if (!message) return null
  return (
    <div className="history-warning-banner" role="status">
      <span aria-hidden="true">⚠</span>
      <span>{message}</span>
    </div>
  )
}
