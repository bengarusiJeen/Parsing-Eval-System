/* StatusPill — header status indicator (idle / loading / ready / error) */

import { useAppState } from '../../state/AppContext'
import type { AppStatus } from '../../state/AppContext'

const LABELS: Record<AppStatus, string> = {
  idle:    'Idle',
  loading: 'Running…',
  ready:   'Results ready',
  error:   'Error',
}

export function StatusPill() {
  const { status } = useAppState()
  return (
    <div id="status-pill" className={`s-${status}`}>
      <span className="s-dot" />
      <span id="status-text">{LABELS[status]}</span>
    </div>
  )
}
