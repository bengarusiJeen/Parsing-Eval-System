/* format.ts — shared formatting/scoring helpers ported from the legacy frontend.
   Pure functions only; no state. */

import type { BlockResult, DiagnosticDocument } from '../types/reports'

export function trunc(s: string, n: number): string {
  if (s == null) return ''
  return s.length > n ? s.slice(0, n) + '…' : s
}

export function fmt(n: number): string {
  return Number(n).toLocaleString()
}

export function pct(rate: number, digits = 1): string {
  return (rate * 100).toFixed(digits) + '%'
}

/** Coverage colour: high is good (green). */
export function coverageColor(rate: number): string {
  return rate >= 0.8 ? 'var(--success)'
       : rate >= 0.5 ? 'var(--warning)'
       :               'var(--danger)'
}

/** "Cleanliness" colour for noise rate: low noise is good. */
export function noiseCleanColor(noiseRate: number): string {
  const clean = 1 - noiseRate
  return clean >= 0.75 ? 'var(--success)'
       : clean >= 0.40 ? 'var(--warning)'
       :                 'var(--danger)'
}

/** 0–100 score colour (used for file tabs + summary). */
export function scoreColor(score: number): string {
  return score >= 75 ? 'var(--success)'
       : score >= 40 ? 'var(--warning)'
       :               'var(--danger)'
}

/** Score number 0–100 derived from a diagnostic-doc's missing/unclass counts. */
export function docScore(doc: DiagnosticDocument | undefined | null): number {
  if (!doc) return 100
  const total = doc.total_missing_ngrams
  if (!total) return 100
  const unc = doc.detected_problems?.UNCLASSIFIED?.count ?? 0
  return Math.round(((total - unc) / total) * 100)
}

/** Total number of detected problems for a diagnostic doc (excluding UNCLASSIFIED). */
export function docIssueCount(doc: DiagnosticDocument | undefined | null): number {
  if (!doc) return 0
  const dp = doc.detected_problems
  return (dp.MISSING_BLOCK_PARSE?.count ?? 0)
       + (dp.OCR_SPLIT?.count           ?? 0)
       + (dp.MERGED_WORDS?.count        ?? 0)
       + (dp.FORMATTING_ISSUES?.count   ?? 0)
}

/** Pull missing ngrams from a block whose key name encodes n (e.g. `missing_trigrams_in_block`). */
export function getMissingNgrams(block: BlockResult): string[] {
  const key = Object.keys(block).find(
    k => k.startsWith('missing_') && k.endsWith('_in_block'),
  )
  if (!key) return []
  const v = (block as Record<string, unknown>)[key]
  return Array.isArray(v) ? (v as string[]) : []
}

/** Rank badge class for the comparison table. */
export function rankBadgeClass(rank: number): string {
  if (rank === 1) return 'cmp-rank-1'
  if (rank === 2) return 'cmp-rank-2'
  if (rank === 3) return 'cmp-rank-3'
  return 'cmp-rank-n'
}
