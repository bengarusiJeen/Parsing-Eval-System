/* HistoryPage — Timeline + Runs sub-views, switched via HistorySubtabs. */

import { useState } from 'react'

import { HistorySubtabs, type HistoryView } from '../components/history/HistorySubtabs'
import { RunsSection } from '../components/history/RunsSection'
import { TimelineSection } from '../components/history/TimelineSection'

export function HistoryPage() {
  const [view, setView] = useState<HistoryView>('timeline')

  return (
    <div className="history-page">
      <header className="history-header">
        <h1>History</h1>
        <p className="history-subtitle">
          Track parser quality over time and inspect past evaluation runs.
        </p>
        <HistorySubtabs active={view} onChange={setView} />
      </header>

      <div className="history-body">
        {view === 'timeline' ? <TimelineSection /> : <RunsSection />}
      </div>
    </div>
  )
}
