/* ReportToggle — General / Postprocessing / Stream toggle + download links.
   Hidden when the Summary ("All Files") tab is active. */

import { useMemo } from 'react'

import { useAppState } from '../../state/AppContext'
import type { ReportType } from '../../state/AppContext'

function makeDataHref(obj: unknown): string {
  return (
    'data:application/json;charset=utf-8,' +
    encodeURIComponent(JSON.stringify(obj, null, 2))
  )
}

interface Opt { id: ReportType; label: string }
const OPTIONS: Opt[] = [
  { id: 'general',        label: 'General Report' },
  { id: 'postprocessing', label: 'Postprocessing' },
  { id: 'stream',         label: 'Stream View' },
]

export function ReportToggle() {
  const {
    activeDoc,
    activeReport,
    setReport,
    general,
    diagnostic,
    general_pp,
    diagnostic_pp,
  } = useAppState()

  if (activeDoc === 'summary') return null

  const isPP     = activeReport === 'postprocessing'
  const isStream = activeReport === 'stream'

  const hrefs = useMemo(() => ({
    general:    general       ? makeDataHref(general)       : '',
    diag:       diagnostic    ? makeDataHref(diagnostic)    : '',
    general_pp: general_pp    ? makeDataHref(general_pp)    : '',
    diag_pp:    diagnostic_pp ? makeDataHref(diagnostic_pp) : '',
  }), [general, diagnostic, general_pp, diagnostic_pp])

  return (
    <div id="toggle-bar">
      <div className="rpt-toggle">
        {OPTIONS.map(o => (
          <button
            key={o.id}
            type="button"
            className={`rpt-opt${activeReport === o.id ? ' active' : ''}`}
            data-report={o.id}
            onClick={() => setReport(o.id)}
          >
            {o.label}
          </button>
        ))}
      </div>

      <div className="toggle-spacer" />

      {!isPP && !isStream && general && (
        <a className="dl-btn" href={hrefs.general} download="general_report.json" title="Download general report JSON">
          <DownloadIcon />
          general_report.json
        </a>
      )}
      {!isPP && !isStream && diagnostic && (
        <a className="dl-btn" href={hrefs.diag} download="diagnostics_report.json" title="Download diagnostics report JSON">
          <DownloadIcon />
          diagnostics_report.json
        </a>
      )}
      {isPP && general_pp && (
        <a className="dl-btn" href={hrefs.general_pp} download="general_report-postprocessing.json" title="Download PP general report JSON">
          <DownloadIcon />
          general_report-postprocessing.json
        </a>
      )}
      {isPP && diagnostic_pp && (
        <a className="dl-btn" href={hrefs.diag_pp} download="diagnostics_report-postprocessing.json" title="Download PP diagnostics report JSON">
          <DownloadIcon />
          diagnostics_report-postprocessing.json
        </a>
      )}
    </div>
  )
}

function DownloadIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
      <path d="M5.5 1V7M5.5 7L3 4.5M5.5 7L8 4.5M1 9.5H10"
            stroke="currentColor" strokeWidth="1.4"
            strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
