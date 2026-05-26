/* RunDetailsPanel — rendered below the RunsTable when a row is selected.
   Diagnostics are NOT loaded by default; clicking "Show diagnostics" triggers
   an explicit re-fetch with include_diagnostics=true. Empty result sets are
   handled gracefully. */

import { useCallback, useEffect, useState } from 'react'

import { ApiError } from '../../api/client'
import { fetchRunDetail } from '../../api/historyApi'
import { coverageColor, noiseCleanColor, pct } from '../../lib/format'
import { parserLabel } from '../../types/parser'
import type { RunDetail } from '../../types/history'

import { StatusBlock } from './StatusBlock'

interface Props {
  runId: number
  onClose: () => void
}

function friendlyApiError(err: unknown): string {
  if (err instanceof ApiError) {
    const body = err.body as { detail?: unknown } | null
    const detail = body?.detail
    if (typeof detail === 'string') return detail
    if (detail && typeof detail === 'object' && 'message' in detail) {
      return String((detail as { message?: unknown }).message ?? err.message)
    }
    return err.message
  }
  if (err instanceof Error) return err.message
  return 'Unknown error'
}

function formatTs(iso: string | null): string {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleString() } catch { return iso }
}

export function RunDetailsPanel({ runId, onClose }: Props) {
  const [run, setRun] = useState<RunDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [diagShown, setDiagShown] = useState(false)
  const [diagLoading, setDiagLoading] = useState(false)

  // Initial fetch (no diagnostics).
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setRun(null)
    setDiagShown(false)
    fetchRunDetail(runId, false)
      .then(d => { if (!cancelled) setRun(d) })
      .catch(err => { if (!cancelled) setError(friendlyApiError(err)) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [runId])

  const loadDiagnostics = useCallback(() => {
    setDiagLoading(true)
    setError(null)
    fetchRunDetail(runId, true)
      .then(d => { setRun(d); setDiagShown(true) })
      .catch(err => setError(friendlyApiError(err)))
      .finally(() => setDiagLoading(false))
  }, [runId])

  if (loading) {
    return (
      <section className="report-section history-run-detail">
        <StatusBlock state="loading" message={`Loading run #${runId}…`} />
      </section>
    )
  }
  if (error) {
    return (
      <section className="report-section history-run-detail">
        <div className="sec-hdr">
          <h3>Run #{runId}</h3>
          <button type="button" className="cmp-view-btn" onClick={onClose}>Close</button>
        </div>
        <StatusBlock state="error" message={error} />
      </section>
    )
  }
  if (!run) return null

  const rows = run.results ?? []

  return (
    <section className="report-section history-run-detail">
      <div className="sec-hdr history-run-detail-hdr">
        <h3>Run #{run.id}</h3>
        <span className={`history-status-pill history-status-pill--${
          run.status === 'completed' ? 'ok'
          : run.status === 'partial' ? 'warn'
          : run.status === 'failed'  ? 'err'
          :                            'info'
        }`}>
          {run.status}
        </span>
        <span className="history-run-meta">
          {run.run_type} · started {formatTs(run.started_at)} · finished {formatTs(run.finished_at)}
        </span>
        <div className="history-run-actions">
          {!diagShown && (
            <button
              type="button"
              className="cmp-view-btn"
              onClick={loadDiagnostics}
              disabled={diagLoading}
            >
              {diagLoading ? 'Loading…' : 'Show diagnostics'}
            </button>
          )}
          <button type="button" className="cmp-view-btn" onClick={onClose}>Close</button>
        </div>
      </div>

      <div className="history-files-chips">
        <span className="metric-label">Selected files ({run.selected_files.length}):</span>
        {run.selected_files.length === 0 && <span className="history-hint">none</span>}
        {run.selected_files.map(f => (
          <span key={f} className="history-file-pill">{f}</span>
        ))}
      </div>

      {rows.length === 0 ? (
        <StatusBlock state="empty" message="No persisted results for this run." />
      ) : (
        <div className="cmp-table-wrap">
          <table className="cmp-table">
            <thead>
              <tr>
                <th>Parser</th>
                <th>File</th>
                <th className="num">Coverage</th>
                <th className="num">Noise</th>
                <th className="num">Avg</th>
                <th className="num">GT words</th>
                <th className="num">Parser words</th>
                {diagShown && <th>Diagnostics</th>}
              </tr>
            </thead>
            <tbody>
              {rows.map(r => (
                <tr key={`${r.parser_name}-${r.file_name}`}>
                  <td><span className="cmp-parser-name">{parserLabel(r.parser_name)}</span></td>
                  <td>{r.file_name}</td>
                  <td className="num" style={{ color: coverageColor(r.coverage_rate),  fontWeight: 600 }}>{pct(r.coverage_rate)}</td>
                  <td className="num" style={{ color: noiseCleanColor(r.noise_rate),    fontWeight: 600 }}>{pct(r.noise_rate)}</td>
                  <td className="num">{pct(r.avg_score)}</td>
                  <td className="num">{r.gt_word_count}</td>
                  <td className="num">{r.parser_word_count}</td>
                  {diagShown && (
                    <td>
                      <details>
                        <summary>{r.diagnostics_json ? 'view' : '—'}</summary>
                        {r.diagnostics_json && (
                          <pre className="history-diag-pre">
                            {JSON.stringify(r.diagnostics_json, null, 2)}
                          </pre>
                        )}
                      </details>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
