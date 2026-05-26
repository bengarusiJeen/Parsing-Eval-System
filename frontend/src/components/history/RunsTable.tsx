/* RunsTable — newest-first list of evaluation runs. Reuses the .cmp-table
   styling for visual consistency with the Compare page. */

import type { RunSummary } from '../../types/history'

interface Props {
  runs: RunSummary[]
  selectedId: number | null
  onSelect: (id: number) => void
  onRefresh: () => void
}

function statusClass(status: string): string {
  switch (status) {
    case 'completed': return 'history-status-pill history-status-pill--ok'
    case 'partial':   return 'history-status-pill history-status-pill--warn'
    case 'failed':    return 'history-status-pill history-status-pill--err'
    case 'running':   return 'history-status-pill history-status-pill--info'
    default:          return 'history-status-pill'
  }
}

function formatStarted(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export function RunsTable({ runs, selectedId, onSelect, onRefresh }: Props) {
  return (
    <div className="cmp-table-section">
      <div className="cmp-table-title">
        Recent runs
        <button
          type="button"
          className="cmp-view-btn history-refresh-btn"
          onClick={onRefresh}
          title="Refresh runs"
        >
          Refresh
        </button>
      </div>
      <div className="cmp-table-wrap">
        <table className="cmp-table">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Started</th>
              <th>Status</th>
              <th>Parsers</th>
              <th className="num">Files</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {runs.length === 0 ? (
              <tr><td colSpan={6} className="cmp-empty">No runs yet.</td></tr>
            ) : runs.map(r => (
              <tr key={r.id} className={selectedId === r.id ? 'history-row-selected' : undefined}>
                <td>#{r.id}</td>
                <td>{formatStarted(r.started_at)}</td>
                <td><span className={statusClass(r.status)}>{r.status}</span></td>
                <td>{r.parsers.join(', ') || '—'}</td>
                <td className="num">{r.files_count}</td>
                <td>
                  <button
                    type="button"
                    className="cmp-view-btn"
                    onClick={() => onSelect(r.id)}
                  >
                    View details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
