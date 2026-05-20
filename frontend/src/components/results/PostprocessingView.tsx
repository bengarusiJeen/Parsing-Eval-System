/* PostprocessingView — per-document PP view, with deltas vs the standard run */

import { useAppState } from '../../state/AppContext'
import { coverageColor, fmt } from '../../lib/format'
import { BlockBreakdown } from './GeneralReportView'
import { DiagnosticCardsForDoc } from './DiagnosticCards'

export function PostprocessingView() {
  const { activeDoc, general, general_pp, diagnostic_pp } = useAppState()
  const idx = typeof activeDoc === 'number' ? activeDoc : -1
  const docs = general_pp?.documents ?? []
  const doc  = idx >= 0 ? docs[idx] : null

  if (!doc) {
    return <p style={{ color: 'var(--text-3)', padding: 8 }}>
      No postprocessing data for this document. Run the evaluation first.
    </p>
  }

  const stdDoc       = (general?.documents ?? [])[idx]
  const stdCov       = stdDoc?.coverage?.coverage_rate ?? null
  const stdNoiseRate = stdDoc?.noise?.noise_rate       ?? null
  const covRate      = doc.coverage.coverage_rate
  const noiseRate    = doc.noise.noise_rate
  const covCol       = coverageColor(covRate)
  const ppDiagDoc    = (diagnostic_pp?.documents ?? [])[idx]

  return (
    <>
      <div className="metrics-row">
        <div className="metric-card mc-coverage" style={{ animationDelay: '0s' }}>
          <div className="metric-label">Coverage (PP)</div>
          <div className="metric-value" style={{ color: covCol }}>
            {(covRate * 100).toFixed(1)}<span className="unit">%</span>
          </div>
          <div className="metric-sub">
            {doc.coverage.total_missing_unique_ngrams_ratio} trigrams missing
            {stdCov !== null && <DeltaInline diff={(covRate - stdCov) * 100} betterWhen="higher" />}
          </div>
        </div>

        <div className="metric-card mc-noise" style={{ animationDelay: '.06s' }}>
          <div className="metric-label">Noise (PP)</div>
          <div className="metric-value" style={{ color: 'var(--danger)' }}>
            {(noiseRate * 100).toFixed(1)}<span className="unit">%</span>
          </div>
          <div className="metric-sub">
            {doc.noise.noise_ratio} parser words are noise
            {stdNoiseRate !== null && <DeltaInline diff={(noiseRate - stdNoiseRate) * 100} betterWhen="lower" />}
          </div>
        </div>

        <div className="metric-card mc-gt" style={{ animationDelay: '.12s' }}>
          <div className="metric-label">GT Words</div>
          <div className="metric-value">{fmt(doc.gt_total_words_non_unique)}</div>
          <div className="metric-sub">ground truth tokens</div>
        </div>

        <div className="metric-card mc-parser" style={{ animationDelay: '.18s' }}>
          <div className="metric-label">Parser Words</div>
          <div className="metric-value">{fmt(doc.parser_total_words_non_unique)}</div>
          <div className="metric-sub">after postprocessing</div>
        </div>
      </div>

      <BlockBreakdown blocks={doc.block_results} label="Block Coverage Breakdown (PP)" />

      {doc.noise.noise_words.length > 0 && (
        <div className="report-section" style={{ animationDelay: '.16s' }}>
          <div className="sec-hdr">
            <h3>Noise Words (PP)</h3>
            <span className="sec-count">{doc.noise.noise_words_count}</span>
          </div>
          <div className="word-cloud">
            {doc.noise.noise_words.map((w, i) => (
              <span key={i} className="tag tag-noise" dir="auto">{w}</span>
            ))}
          </div>
        </div>
      )}

      {ppDiagDoc && (
        <div style={{ marginTop: 28 }}>
          <div className="agg-diag-hdr">
            <h2>Diagnostic Report — Post-Processed</h2>
            <span className="agg-sub">issues remaining after postprocessing</span>
          </div>
          <DiagnosticCardsForDoc doc={ppDiagDoc} />
        </div>
      )}
    </>
  )
}

function DeltaInline({ diff, betterWhen }: { diff: number; betterWhen: 'higher' | 'lower' }) {
  const sign = diff >= 0 ? '+' : ''
  const goodWhenPositive = betterWhen === 'higher'
  const color =
    diff === 0 ? 'var(--text-3)'
      : (diff > 0) === goodWhenPositive ? 'var(--success)' : 'var(--danger)'
  return (
    <span style={{ fontSize: '0.85rem', color, marginLeft: 8 }}>
      ({sign}{diff.toFixed(1)}% vs standard)
    </span>
  )
}
