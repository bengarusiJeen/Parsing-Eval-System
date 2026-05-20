/* SummaryView — cross-document "All Files" summary.
   Has two sub-tabs: File Overview (default) and Global Summary (if PP data exists). */

import { useEffect, useRef } from 'react'

import { useAppState } from '../../state/AppContext'
import {
  coverageColor,
  docIssueCount,
  docScore,
  scoreColor,
  trunc,
} from '../../lib/format'
import { DiagnosticCardsAggregated } from './DiagnosticCards'
import type {
  DiagnosticDocument,
  DocumentReport,
} from '../../types/reports'

export function SummaryView() {
  const {
    general,
    general_pp,
    activeSummaryTab,
    setSummaryTab,
  } = useAppState()

  const genDocs = general?.documents ?? []
  const n       = genDocs.length
  const hasPP   = (general_pp?.documents ?? []).length > 0

  if (!n) {
    return <p style={{ color: 'var(--text-3)', padding: 8 }}>No data available.</p>
  }

  return (
    <>
      {hasPP && (
        <div className="sum-subtabs">
          <button
            type="button"
            className={`sum-opt${activeSummaryTab === 'files' ? ' sum-opt-active' : ''}`}
            onClick={() => setSummaryTab('files')}
          >
            File Overview
          </button>
          <button
            type="button"
            className={`sum-opt${activeSummaryTab === 'global' ? ' sum-opt-active' : ''}`}
            onClick={() => setSummaryTab('global')}
          >
            Global Summary
          </button>
        </div>
      )}

      {activeSummaryTab === 'global' && hasPP ? <GlobalSummary /> : <FileOverview />}
    </>
  )
}

/* ══════════════════════════════════════════════════════════════
   FILE OVERVIEW (default sub-tab)
══════════════════════════════════════════════════════════════ */

function FileOverview() {
  const { general, diagnostic, selectDoc } = useAppState()

  const genDocs  = general?.documents    ?? []
  const diagDocs = diagnostic?.documents ?? []
  const n        = genDocs.length

  /* Aggregate numbers */
  let totalCov     = 0
  let criticalFiles = 0
  const issueCounts = {
    MISSING_BLOCK_PARSE: 0,
    OCR_SPLIT:           0,
    MERGED_WORDS:        0,
    FORMATTING_ISSUES:   0,
    UNCLASSIFIED:        0,
  }

  genDocs.forEach(doc => {
    totalCov += doc.coverage.coverage_rate
    if (doc.coverage.coverage_rate < 0.5) criticalFiles++
  })

  diagDocs.forEach(doc => {
    const dp = doc.detected_problems
    issueCounts.MISSING_BLOCK_PARSE += dp.MISSING_BLOCK_PARSE?.count ?? 0
    issueCounts.OCR_SPLIT           += dp.OCR_SPLIT?.count           ?? 0
    issueCounts.MERGED_WORDS        += dp.MERGED_WORDS?.count        ?? 0
    issueCounts.FORMATTING_ISSUES   += dp.FORMATTING_ISSUES?.count   ?? 0
    issueCounts.UNCLASSIFIED        += dp.UNCLASSIFIED?.count        ?? 0
  })

  const totalIssues =
    issueCounts.MISSING_BLOCK_PARSE +
    issueCounts.OCR_SPLIT +
    issueCounts.MERGED_WORDS +
    issueCounts.FORMATTING_ISSUES

  const avgCovRate = totalCov / n
  const avgCov     = (avgCovRate * 100).toFixed(1)
  const avgColor   = coverageColor(avgCovRate)

  const distCategories = [
    { label: 'Missing Block', count: issueCounts.MISSING_BLOCK_PARSE, color: 'var(--c-missing)', delay: '0s' },
    { label: 'OCR Split',     count: issueCounts.OCR_SPLIT,           color: 'var(--c-ocr)',     delay: '0.06s' },
    { label: 'Merged Words',  count: issueCounts.MERGED_WORDS,        color: 'var(--c-merged)',  delay: '0.12s' },
    { label: 'Formatting',    count: issueCounts.FORMATTING_ISSUES,   color: 'var(--c-format)',  delay: '0.18s' },
    { label: 'Unclassified',  count: issueCounts.UNCLASSIFIED,        color: 'var(--c-unclass)', delay: '0.24s' },
  ]
  const maxIssue = Math.max(1, ...distCategories.map(c => c.count))

  /* Animate bars after mount */
  const rootRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    requestAnimationFrame(() => {
      rootRef.current?.querySelectorAll<HTMLDivElement>('.fh-bar-fill, .dist-bar-fill')
        .forEach(el => {
          const w = el.dataset.w || '0'
          el.style.width = `${w}%`
        })
    })
  })

  return (
    <div ref={rootRef}>
      <div className="summary-metrics">
        <MetricCard label="Avg Coverage" value={avgCov} unit="%" sub={`across ${n} document${n !== 1 ? 's' : ''}`} color={avgColor} delay={0} kind="coverage" />
        <MetricCard label="Total Issues" value={String(totalIssues)} sub="detected problems"
                    color={totalIssues > 0 ? 'var(--danger)' : 'var(--success)'} delay={0.06} kind="noise" />
        <MetricCard label="Documents" value={String(n)} sub="files evaluated" delay={0.12} kind="gt" />
        <MetricCard label="Critical Files" value={String(criticalFiles)} sub="coverage < 50%"
                    color={criticalFiles > 0 ? 'var(--danger)' : 'var(--success)'} delay={0.18} kind="parser" />
      </div>

      <div className="summary-body">
        <FileHealthTable docs={genDocs} diagDocs={diagDocs} onSelect={selectDoc} />

        <div className="issue-dist">
          <div className="issue-dist-title">Issue Distribution</div>
          {distCategories.map(c => (
            <div key={c.label} className="dist-row">
              <div className="dist-label">{c.label}</div>
              <div className="dist-bar-track">
                <div className="dist-bar-fill"
                     data-w={(c.count / maxIssue * 100).toFixed(1)}
                     style={{
                       background: c.color,
                       ['--bar-delay' as string]: c.delay,
                     } as React.CSSProperties} />
              </div>
              <div className="dist-count">{c.count}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="agg-diag-hdr">
        <h2>Diagnostic Report — All Files</h2>
        <span className="agg-sub">
          {totalIssues} issues across {n} document{n !== 1 ? 's' : ''}
        </span>
      </div>

      <DiagnosticCardsAggregated docs={diagDocs} counts={issueCounts} />
    </div>
  )
}

/* ── File health table ───────────────────────────────────────── */

function FileHealthTable({ docs, diagDocs, onSelect }: {
  docs:     DocumentReport[]
  diagDocs: DiagnosticDocument[]
  onSelect: (idx: number) => void
}) {
  return (
    <div className="fh-table">
      <div className="fh-table-header">
        <div>Document</div>
        <div>Coverage</div>
        <div style={{ textAlign: 'right' }}>Issues</div>
        <div style={{ textAlign: 'right' }}>Score</div>
      </div>
      {docs.map((doc, i) => {
        const cov     = doc.coverage.coverage_rate
        const pctStr  = (cov * 100).toFixed(1)
        const color   = coverageColor(cov)
        const dd      = diagDocs[i]
        const issues  = docIssueCount(dd)
        const score   = dd ? docScore(dd) : Math.round(cov * 100)
        const scColor = scoreColor(score)
        const ext     = dd?.file_ext ?? ''
        return (
          <div
            key={`${doc.doc_name}-${i}`}
            className="fh-row"
            onClick={() => onSelect(i)}
            title={doc.doc_name}
          >
            <div className="fh-name">
              {trunc(doc.doc_name, 28)}
              {ext && <span className="fh-name-ext">{ext}</span>}
            </div>
            <div className="fh-bar-wrap">
              <div className="fh-bar-track">
                <div className="fh-bar-fill" data-w={pctStr} style={{ background: color }} />
              </div>
              <div className="fh-pct" style={{ color }}>{pctStr}%</div>
            </div>
            <div
              className="fh-issues"
              style={{ color: issues > 0 ? 'var(--danger)' : 'var(--text-3)' }}
            >
              {issues > 0 ? issues : '—'}
            </div>
            <div className="fh-score" style={{ color: scColor }}>{score}</div>
          </div>
        )
      })}
    </div>
  )
}

/* ── Metric card helper ──────────────────────────────────────── */

type MetricKind = 'coverage' | 'noise' | 'gt' | 'parser'

function MetricCard({ label, value, unit, sub, color, delay = 0, kind }: {
  label: string
  value: string
  unit?: string
  sub?:  React.ReactNode
  color?: string
  delay?: number
  kind:  MetricKind
}) {
  return (
    <div className={`metric-card mc-${kind}`} style={{ animationDelay: `${delay}s` }}>
      <div className="metric-label">{label}</div>
      <div className="metric-value" style={color ? { color } : undefined}>
        {value}
        {unit && <span className="unit">{unit}</span>}
      </div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   GLOBAL SUMMARY (sub-tab, only when PP data exists)
══════════════════════════════════════════════════════════════ */

function GlobalSummary() {
  const { general, general_pp, diagnostic, diagnostic_pp } = useAppState()

  const stdDocs = general?.documents       ?? []
  const ppDocs  = general_pp?.documents    ?? []
  const stdDiag = diagnostic?.documents    ?? []
  const ppDiag  = diagnostic_pp?.documents ?? []
  const n       = ppDocs.length

  const rootRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    requestAnimationFrame(() => {
      rootRef.current?.querySelectorAll<HTMLDivElement>('.cmp-bar-fill')
        .forEach(el => {
          el.style.width = `${el.dataset.w || '0'}%`
        })
    })
  })

  if (!n) {
    return <p style={{ color: 'var(--text-3)', padding: 8 }}>
      No postprocessing data available.
    </p>
  }

  /* Global averages */
  let sumCovBefore   = 0, sumCovAfter   = 0
  let sumNoiseBefore = 0, sumNoiseAfter = 0
  stdDocs.forEach(d => { sumCovBefore += d.coverage.coverage_rate; sumNoiseBefore += d.noise.noise_rate })
  ppDocs.forEach(d  => { sumCovAfter  += d.coverage.coverage_rate; sumNoiseAfter  += d.noise.noise_rate })

  const avgCovBefore   = sumCovBefore   / n
  const avgCovAfter    = sumCovAfter    / n
  const avgNoiseBefore = sumNoiseBefore / n
  const avgNoiseAfter  = sumNoiseAfter  / n

  const covDelta   = (avgCovAfter  - avgCovBefore)   * 100
  const noiseDelta = (avgNoiseAfter - avgNoiseBefore) * 100

  const diagCategories = [
    { key: 'MISSING_BLOCK_PARSE', name: 'Missing Blocks', color: 'var(--c-missing)' },
    { key: 'OCR_SPLIT',           name: 'OCR Splits',     color: 'var(--c-ocr)'     },
    { key: 'MERGED_WORDS',        name: 'Merged Words',   color: 'var(--c-merged)'  },
    { key: 'FORMATTING_ISSUES',   name: 'Formatting',     color: 'var(--c-format)'  },
    { key: 'UNCLASSIFIED',        name: 'Unclassified',   color: 'var(--c-unclass)' },
  ] as const

  /* Noise scaling - use max across all values to keep bars comparable */
  const maxNoise = Math.max(
    0.01,
    ...ppDocs.map((d, i) => Math.max(d.noise.noise_rate, stdDocs[i]?.noise?.noise_rate ?? 0)),
  ) * 100

  return (
    <div ref={rootRef}>
      <div className="metrics-row" style={{ marginBottom: 24 }}>
        <MetricCard label="Coverage — Before" value={(avgCovBefore * 100).toFixed(1)} unit="%"
                    sub="baseline average" color={coverageColor(avgCovBefore)} delay={0} kind="coverage" />
        <MetricCard label="Coverage — After"  value={(avgCovAfter * 100).toFixed(1)}  unit="%"
                    sub={<><DeltaSpan diff={covDelta} betterWhen="higher" />{' vs baseline'}</>}
                    color={coverageColor(avgCovAfter)} delay={0.06} kind="coverage" />
        <MetricCard label="Noise Rate — Before" value={(avgNoiseBefore * 100).toFixed(1)} unit="%"
                    sub="baseline average" color="var(--danger)" delay={0.12} kind="noise" />
        <MetricCard label="Noise Rate — After"  value={(avgNoiseAfter * 100).toFixed(1)}  unit="%"
                    sub={<><DeltaSpan diff={noiseDelta} betterWhen="lower" />{' vs baseline'}</>}
                    color="var(--danger)" delay={0.18} kind="noise" />
      </div>

      {/* Coverage comparison */}
      <div className="report-section" style={{ animationDelay: '.08s' }}>
        <div className="sec-hdr">
          <h3>Coverage — Before vs After</h3>
          <span className="sec-count">{n} document{n !== 1 ? 's' : ''}</span>
        </div>
        {ppDocs.map((ppDoc, i) => {
          const stdDoc = stdDocs[i]
          const before = stdDoc ? stdDoc.coverage.coverage_rate * 100 : 0
          const after  = ppDoc.coverage.coverage_rate * 100
          const delta  = after - before
          return (
            <BeforeAfterRow key={i} name={ppDoc.doc_name} delta={delta} betterWhen="higher">
              <BarRow label="Before" w={before.toFixed(1)} pct={before} valueColor={coverageColor(before / 100)} fillStyle={{ background: 'var(--text-3)', opacity: 0.55 }} />
              <BarRow label="After"  w={after.toFixed(1)}  pct={after}  valueColor={coverageColor(after  / 100)} fillStyle={{ background: coverageColor(after / 100) }} />
            </BeforeAfterRow>
          )
        })}
      </div>

      {/* Noise comparison */}
      <div className="report-section" style={{ animationDelay: '.14s' }}>
        <div className="sec-hdr">
          <h3>Noise Rate — Before vs After</h3>
          <span className="sec-count">{n} document{n !== 1 ? 's' : ''}</span>
        </div>
        {ppDocs.map((ppDoc, i) => {
          const stdDoc  = stdDocs[i]
          const before  = stdDoc ? stdDoc.noise.noise_rate * 100 : 0
          const after   = ppDoc.noise.noise_rate * 100
          const delta   = after - before
          const afterClr = delta <= 0 ? 'var(--success)' : 'var(--danger)'
          return (
            <BeforeAfterRow key={i} name={ppDoc.doc_name} delta={delta} betterWhen="lower">
              <BarRow label="Before"
                      w={(before / maxNoise * 100).toFixed(1)}
                      pct={before}
                      valueColor="var(--danger)"
                      fillStyle={{ background: 'rgba(255,77,109,0.45)' }} />
              <BarRow label="After"
                      w={(after / maxNoise * 100).toFixed(1)}
                      pct={after}
                      valueColor={afterClr}
                      fillStyle={{ background: afterClr }} />
            </BeforeAfterRow>
          )
        })}
      </div>

      {/* Diagnostic improvement */}
      <div className="report-section" style={{ animationDelay: '.20s' }}>
        <div className="sec-hdr">
          <h3>Diagnostic Improvement Analysis</h3>
          <span className="sec-count">all categories</span>
        </div>
        <div style={{ paddingTop: 4 }}>
          {diagCategories.map(cat => {
            const getCount = (d: DiagnosticDocument): number => {
              const dp = d.detected_problems as unknown as Record<string, { count?: number }>
              return dp[cat.key]?.count ?? 0
            }
            const before = stdDiag.reduce((s, d) => s + getCount(d), 0)
            const after  = ppDiag.reduce( (s, d) => s + getCount(d), 0)
            const diff       = before - after
            const pctVal     = before > 0 ? (diff / before * 100).toFixed(0) : null
            const afterColor =
              after < before ? 'var(--success)' :
              after > before ? 'var(--danger)'  :
                               'var(--text-2)'
            const { label, style } = resolutionTag(diff, pctVal)
            return (
              <div key={cat.key} className="diag-cmp-row">
                <div className="diag-cmp-name">
                  <div className="diag-cmp-dot" style={{ background: cat.color }} />
                  {cat.name}
                </div>
                <div className="diag-cmp-count">
                  {before} issue{before !== 1 ? 's' : ''}
                </div>
                <div className="diag-cmp-arrow">→</div>
                <div className="diag-cmp-count" style={{ color: afterColor }}>
                  {after} issue{after !== 1 ? 's' : ''}
                </div>
                <div className="diag-cmp-resolution" style={style}>{label}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function resolutionTag(diff: number, pct: string | null): {
  label: string
  style: React.CSSProperties
} {
  if (pct === null) return { label: 'no data', style: { background: 'var(--surface-3)', color: 'var(--text-3)' } }
  if (diff > 0)    return { label: `${pct}% resolved`,    style: { background: 'rgba(21,128,61,0.08)',  color: '#15803d' } }
  if (diff < 0)    return { label: `${Math.abs(+pct)}% increase`, style: { background: 'rgba(185,28,28,0.08)', color: '#b91c1c' } }
  return { label: 'no change', style: { background: 'var(--surface-3)', color: 'var(--text-3)' } }
}

function BeforeAfterRow({ name, delta, betterWhen, children }: {
  name:       string
  delta:      number
  betterWhen: 'higher' | 'lower'
  children:   React.ReactNode
}) {
  const sign = delta >= 0 ? '+' : ''
  const color =
    delta === 0 ? 'var(--text-3)'
      : (delta > 0) === (betterWhen === 'higher') ? 'var(--success)' : 'var(--danger)'
  return (
    <div className="cmp-row">
      <div className="cmp-name" title={name}>{trunc(name, 22)}</div>
      <div className="cmp-bars">{children}</div>
      <div className="cmp-delta" style={{ color }}>
        {sign}{delta.toFixed(1)}%
      </div>
    </div>
  )
}

function BarRow({ label, w, pct, valueColor, fillStyle }: {
  label:      string
  w:          string
  pct:        number
  valueColor: string
  fillStyle:  React.CSSProperties
}) {
  return (
    <div className="cmp-bar-group">
      <div className="cmp-bar-label-sm">{label}</div>
      <div className="cmp-bar-track">
        <div className="cmp-bar-fill" data-w={w} style={fillStyle} />
      </div>
      <div className="cmp-bar-val" style={{ color: valueColor }}>{pct.toFixed(1)}%</div>
    </div>
  )
}

function DeltaSpan({ diff, betterWhen }: { diff: number; betterWhen: 'higher' | 'lower' }) {
  const sign = diff >= 0 ? '+' : ''
  const color =
    diff === 0 ? 'var(--text-3)'
      : (diff > 0) === (betterWhen === 'higher') ? 'var(--success)' : 'var(--danger)'
  return <span style={{ color }}>{sign}{diff.toFixed(1)}%</span>
}
