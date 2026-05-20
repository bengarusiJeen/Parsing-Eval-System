/* GeneralReportView — per-document "General Report" view (metrics + blocks + noise + diagnostic) */

import { useState, useEffect, useRef } from 'react'

import { useAppState } from '../../state/AppContext'
import {
  coverageColor,
  fmt,
  getMissingNgrams,
  pct,
} from '../../lib/format'
import type { BlockResult } from '../../types/reports'
import { DiagnosticCardsForDoc } from './DiagnosticCards'

export function GeneralReportView() {
  const { activeDoc, general, diagnostic } = useAppState()
  const idx  = typeof activeDoc === 'number' ? activeDoc : -1
  const docs = general?.documents ?? []
  const doc  = idx >= 0 ? docs[idx] : null

  if (!doc) {
    return <p style={{ color: 'var(--text-3)', padding: 8 }}>
      No general report data for this document.
    </p>
  }

  const covPct   = pct(doc.coverage.coverage_rate)
  const noisePct = pct(doc.noise.noise_rate)
  const covCol   = coverageColor(doc.coverage.coverage_rate)

  const diagDoc = (diagnostic?.documents ?? [])[idx]

  return (
    <>
      {/* Metrics row */}
      <div className="metrics-row">
        <div className="metric-card mc-coverage" style={{ animationDelay: '0s' }}>
          <div className="metric-label">Coverage</div>
          <div className="metric-value" style={{ color: covCol }}>
            {(doc.coverage.coverage_rate * 100).toFixed(1)}
            <span className="unit">%</span>
          </div>
          <div className="metric-sub">
            {doc.coverage.total_missing_unique_ngrams_ratio} trigrams missing
          </div>
        </div>
        <div className="metric-card mc-noise" style={{ animationDelay: '.06s' }}>
          <div className="metric-label">Noise</div>
          <div className="metric-value" style={{ color: 'var(--danger)' }}>
            {(doc.noise.noise_rate * 100).toFixed(1)}
            <span className="unit">%</span>
          </div>
          <div className="metric-sub">
            {doc.noise.noise_ratio} parser words are noise
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
          <div className="metric-sub">parser output tokens</div>
        </div>
      </div>

      {/* Block breakdown */}
      <BlockBreakdown blocks={doc.block_results} />

      {/* Noise words */}
      {doc.noise.noise_words.length > 0 && (
        <div className="report-section" style={{ animationDelay: '.16s' }}>
          <div className="sec-hdr">
            <h3>Noise Words</h3>
            <span className="sec-count">{doc.noise.noise_words_count}</span>
          </div>
          <div className="word-cloud">
            {doc.noise.noise_words.map((w, i) => (
              <span key={i} className="tag tag-noise" dir="auto">{w}</span>
            ))}
          </div>
        </div>
      )}

      {/* Embedded diagnostic report */}
      {diagDoc && (
        <div style={{ marginTop: 28 }}>
          <div className="agg-diag-hdr">
            <h2>Diagnostic Report</h2>
            <span className="agg-sub">detected parsing issues</span>
          </div>
          <DiagnosticCardsForDoc doc={diagDoc} />
        </div>
      )}

      {/* unused (suppress) */}
      <span hidden>{covPct}{noisePct}</span>
    </>
  )
}

/* ── Block breakdown (collapsible per-row missing-ngrams list) ───── */

export function BlockBreakdown({ blocks, label = 'Block Coverage Breakdown' }:
  { blocks: BlockResult[]; label?: string }) {
  return (
    <div className="report-section" style={{ animationDelay: '.08s' }}>
      <div className="sec-hdr">
        <h3>{label}</h3>
        <span className="sec-count">{blocks.length} blocks</span>
      </div>
      {blocks.map((b, i) => <BlockRow key={i} block={b} />)}
    </div>
  )
}

function BlockRow({ block }: { block: BlockResult }) {
  const [open, setOpen] = useState(false)
  const rate  = block.coverage.coverage_rate
  const color = coverageColor(rate)
  const pctStr= (rate * 100).toFixed(1)
  const missing = getMissingNgrams(block)

  const barRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    requestAnimationFrame(() => {
      if (barRef.current) barRef.current.style.width = `${pctStr}%`
    })
  }, [pctStr])

  return (
    <>
      <div className="block-row" onClick={() => missing.length && setOpen(o => !o)}>
        <div className="blk-label">Block {block.block_index}</div>
        <div className="blk-bar-track">
          <div ref={barRef} className="blk-bar-fill" style={{ background: color, width: '0%' }} />
        </div>
        <div className="blk-ratio">{block.coverage.total_missing_unique_ngrams_ratio}</div>
        <div className="blk-pct" style={{ color }}>{pctStr}%</div>
      </div>
      {missing.length > 0 && (
        <div className={`blk-missing${open ? ' open' : ''}`}>
          {missing.map((w, i) => (
            <span key={i} className="tag tag-missing" dir="auto">{w}</span>
          ))}
        </div>
      )}
    </>
  )
}
