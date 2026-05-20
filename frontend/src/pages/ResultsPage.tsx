/* ResultsPage — the multi-state Results view (empty / loading / error / report). */

import { useAppState } from '../state/AppContext'
import { ParserSubtabs }      from '../components/results/ParserSubtabs'
import { FileTabs }           from '../components/results/FileTabs'
import { ReportToggle }       from '../components/results/ReportToggle'
import { SummaryView }        from '../components/results/SummaryView'
import { GeneralReportView }  from '../components/results/GeneralReportView'
import { PostprocessingView } from '../components/results/PostprocessingView'
import { StreamComparisonView } from '../components/results/StreamComparisonView'
import { parserLabel }        from '../types/parser'

export function ResultsPage() {
  const {
    status,
    errorLog,
    stdoutLog,
    activeDoc,
    activeReport,
    activeParser,
    parserResults,
    general,
  } = useAppState()

  // For the failed-parser case in multi-parser mode
  let parserFailContent: React.ReactNode = null
  if (activeParser !== null && parserResults[activeParser]) {
    const d = parserResults[activeParser]
    if (d.status !== 'ok') {
      parserFailContent = (
        <div className="parser-fail-panel">
          <div className="parser-fail-icon">⚠</div>
          <div className="parser-fail-title">
            {parserLabel(activeParser)} — Parser Failed
          </div>
          <pre className="parser-fail-log">
            {d.stderr || d.error || 'No error details available.'}
          </pre>
        </div>
      )
    }
  }

  const showReportPanel = status === 'ready' && general && !parserFailContent

  return (
    <div id="results-wrap">
      {/* Show parser subtabs whenever multi-parser data exists */}
      <ParserSubtabs />

      {/* File tabs + toggle bar only shown when we have data to view */}
      {showReportPanel && <FileTabs />}
      {showReportPanel && <ReportToggle />}

      <main id="content">
        {status === 'idle' && (
          <div id="empty-state">
            <div className="empty-icon-ring">◈</div>
            <div className="empty-title">
              No results <span className="accent-char">yet</span>
            </div>
            <div className="empty-divider" />
            <div className="empty-sub">
              Select files and a parser, then click <strong>Start Evaluation</strong>.<br />
              Coverage, noise, and diagnostic reports will appear here.
            </div>
          </div>
        )}

        {status === 'loading' && (
          <div id="loading-state">
            <div className="load-spinner" />
            <div className="load-title">Running evaluation…</div>
            <pre id="stdout-log">{stdoutLog || ' '}</pre>
          </div>
        )}

        {status === 'error' && (
          <div id="error-state">
            <div style={{
              fontFamily: 'var(--f-display)',
              fontSize: '1rem',
              fontWeight: 600,
              color: 'var(--danger)',
            }}>
              Evaluation failed
            </div>
            <pre id="error-log" className="error-box">{errorLog}</pre>
          </div>
        )}

        {parserFailContent && <div id="report-panel">{parserFailContent}</div>}

        {showReportPanel && (
          <div id="report-panel">
            {activeReport === 'stream' ? (
              <StreamComparisonView />
            ) : activeReport === 'postprocessing' ? (
              activeDoc === 'summary'
                ? <SummaryView /> /* show summary even on PP toggle from summary */
                : <PostprocessingView />
            ) : activeDoc === 'summary' ? (
              <SummaryView />
            ) : (
              <GeneralReportView />
            )}
          </div>
        )}
      </main>
    </div>
  )
}
