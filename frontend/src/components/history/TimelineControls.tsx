/* TimelineControls — parser / metric / mode / limit + conditional Files multi-select
   or Corpus dropdown. Stateless: the parent (TimelineSection) owns selection state. */

import { PARSERS } from '../../types/parser'
import type { Corpus } from '../../types/corpus'
import type { TimelineMetric, TimelineMode } from '../../types/history'
import type { FileEntry } from '../../types/file'

interface Props {
  selectedParsers: Set<string>
  onToggleParser: (id: string) => void

  metric: TimelineMetric
  onMetricChange: (m: TimelineMetric) => void

  mode: TimelineMode
  onModeChange: (m: TimelineMode) => void

  limit: number
  onLimitChange: (l: number) => void

  // Files mode
  availableFiles: FileEntry[]
  selectedFiles: Set<string>
  onToggleFile: (name: string) => void

  // Corpus mode
  corpora: Corpus[]
  corporaLoading: boolean
  corporaError: string | null
  selectedCorpusId: number | null
  onCorpusChange: (id: number | null) => void
}

const METRIC_OPTS: { id: TimelineMetric; label: string }[] = [
  { id: 'avg_score', label: 'Avg Score' },
  { id: 'coverage',  label: 'Coverage'  },
  { id: 'noise',     label: 'Noise'     },
]

const MODE_OPTS: { id: TimelineMode; label: string }[] = [
  { id: 'all',     label: 'All Files'        },
  { id: 'files',   label: 'Selected Files'   },
  { id: 'corpus',  label: 'Corpus'           },
  { id: 'overall', label: 'Overall Weighted' },
]

const LIMIT_OPTS = [7, 14, 30]

export function TimelineControls(props: Props) {
  const {
    selectedParsers, onToggleParser,
    metric, onMetricChange,
    mode, onModeChange,
    limit, onLimitChange,
    availableFiles, selectedFiles, onToggleFile,
    corpora, corporaLoading, corporaError,
    selectedCorpusId, onCorpusChange,
  } = props

  const metricLocked = mode === 'overall'

  return (
    <div className="history-controls">
      <div className="history-control history-control--wide">
        <span className="metric-label">Parsers</span>
        <div className="history-files-wrap">
          {PARSERS.map(p => {
            const checked = selectedParsers.has(p.id)
            const disabled = !p.available
            return (
              <label
                key={p.id}
                className={
                  `cmp-check-pill${checked ? ' checked' : ''}` +
                  (disabled ? ' cmp-check-pill--disabled' : '')
                }
                title={disabled ? `${p.label} is not available` : undefined}
                onClick={e => {
                  if (disabled) return
                  e.preventDefault()
                  onToggleParser(p.id)
                }}
              >
                <input type="checkbox" readOnly checked={checked} disabled={disabled} />
                <span>{p.label}{disabled ? ' (unavailable)' : ''}</span>
              </label>
            )
          })}
        </div>
      </div>

      <div className="history-control">
        <span className="metric-label">Metric{metricLocked ? ' (locked)' : ''}</span>
        <div className="rpt-toggle">
          {METRIC_OPTS.map(o => (
            <button
              key={o.id}
              type="button"
              className={`rpt-opt${metric === o.id ? ' active' : ''}`}
              disabled={metricLocked}
              onClick={() => !metricLocked && onMetricChange(o.id)}
              title={metricLocked ? 'Overall mode always shows Avg Score' : undefined}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      <div className="history-control">
        <span className="metric-label">Mode</span>
        <div className="rpt-toggle">
          {MODE_OPTS.map(o => (
            <button
              key={o.id}
              type="button"
              className={`rpt-opt${mode === o.id ? ' active' : ''}`}
              onClick={() => onModeChange(o.id)}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      <div className="history-control">
        <label className="metric-label" htmlFor="tl-limit">Limit</label>
        <select
          id="tl-limit"
          className="history-select"
          value={limit}
          onChange={e => onLimitChange(Number(e.target.value))}
        >
          {LIMIT_OPTS.map(n => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>

      {mode === 'files' && (
        <div className="history-control history-control--wide">
          <span className="metric-label">Files</span>
          <div className="history-files-wrap">
            {availableFiles.length === 0 && (
              <span className="history-hint">No files available.</span>
            )}
            {availableFiles.map(f => {
              const checked = selectedFiles.has(f.name)
              return (
                <label
                  key={f.name}
                  className={`cmp-check-pill${checked ? ' checked' : ''}`}
                  onClick={e => { e.preventDefault(); onToggleFile(f.name) }}
                >
                  <input type="checkbox" readOnly checked={checked} />
                  <span>{f.name}</span>
                </label>
              )
            })}
          </div>
        </div>
      )}

      {mode === 'corpus' && (
        <div className="history-control">
          <label className="metric-label" htmlFor="tl-corpus">Corpus</label>
          {corporaLoading ? (
            <span className="history-hint">Loading corpora…</span>
          ) : corporaError ? (
            <span className="history-status history-status--error">{corporaError}</span>
          ) : (
            <select
              id="tl-corpus"
              className="history-select"
              value={selectedCorpusId ?? ''}
              onChange={e =>
                onCorpusChange(e.target.value === '' ? null : Number(e.target.value))
              }
            >
              <option value="">— pick a corpus —</option>
              {corpora.map(c => (
                <option key={c.id} value={c.id}>
                  {c.name} (ratio {c.overall_ratio})
                </option>
              ))}
            </select>
          )}
        </div>
      )}
    </div>
  )
}
