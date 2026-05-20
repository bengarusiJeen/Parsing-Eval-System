/* DiagnosticCards — accordion view of detected_problems.
   Used by GeneralReportView, PostprocessingView, and the aggregated SummaryView. */

import { useState, type ReactNode } from 'react'

import { trunc } from '../../lib/format'
import type {
  DiagnosticDocument,
  DetectedProblems,
  FormattingIssue,
  MergedWordIssue,
  OcrSplitIssue,
} from '../../types/reports'

/* ── Card shell ──────────────────────────────────────────────── */

interface CardProps {
  color:    string
  count:    number
  name:     string
  desc:     string
  delaySec: number
  children: ReactNode
}

function DiagCard({ color, count, name, desc, delaySec, children }: CardProps) {
  const [open, setOpen] = useState(false)
  return (
    <div
      className={`diag-card${open ? ' open' : ''}`}
      style={{ animationDelay: `${delaySec}s` }}
    >
      <div className="diag-hdr" onClick={() => setOpen(o => !o)}>
        <div className="diag-stripe" style={{ background: color }} />
        <div className="diag-num"    style={{ color }}>{count}</div>
        <div className="diag-meta">
          <div className="diag-meta-name">{name}</div>
          <div className="diag-meta-desc">{desc}</div>
        </div>
        <div className="diag-chevron">▼</div>
      </div>
      <div className="diag-body">
        <div className="diag-inner">
          {count === 0 ? (
            <div className="diag-empty">No issues detected.</div>
          ) : children}
        </div>
      </div>
    </div>
  )
}

/* ── Per-issue body renderers ────────────────────────────────── */

function MissingBlocksBody({ blocks }: { blocks: number[] }) {
  return (
    <div className="block-pills">
      {blocks.map(n => (
        <span key={n} className="block-pill">Block {n}</span>
      ))}
    </div>
  )
}

function OcrSplitsBody({ issues }: { issues: OcrSplitIssue[] }) {
  return (
    <div className="issue-list">
      {issues.map((issue, i) => {
        const word  = issue.original_word ?? issue.word ?? '?'
        const frags = issue.fragments_in_parser ?? issue.fragments ?? []
        return (
          <div key={i} className="ocr-item">
            <span className="ocr-word" dir="auto">{word}</span>
            <span className="arr">→</span>
            <div className="ocr-frags">
              {frags.map((f, j) => (
                <span key={j} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                  {j > 0 && <span className="chip-plus">+</span>}
                  <span className="frag-chip" dir="auto">{f}</span>
                </span>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function MergedWordsBody({ issues }: { issues: MergedWordIssue[] }) {
  return (
    <div className="issue-list">
      {issues.map((issue, i) => (
        <div key={i} className="merge-item">
          <div className="orig-chips">
            {(issue.original ?? []).map((p, j) => (
              <span key={j} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                {j > 0 && <span className="chip-plus">+</span>}
                <span className="orig-chip" dir="auto">{p}</span>
              </span>
            ))}
          </div>
          <span className="arr">→</span>
          <span className="merged-chip" dir="auto">{issue.merged_word}</span>
        </div>
      ))}
    </div>
  )
}

function FormattingBody({ data }: { data: DetectedProblems['FORMATTING_ISSUES'] }) {
  const reversals = data.WORD_ORDER_REVERSAL?.issues   ?? []
  const punct     = data.MISPLACED_PUNCTUATION?.issues ?? []
  return (
    <>
      {reversals.length > 0 && (
        <>
          <div className="sub-hdr">Word Order Reversals <span>{reversals.length}</span></div>
          <div className="issue-list">
            {reversals.map((issue, i) => (
              <FmtItem key={i} issue={issue} kind="reversal" />
            ))}
          </div>
        </>
      )}
      {punct.length > 0 && (
        <>
          <div className="sub-hdr">Misplaced Punctuation <span>{punct.length}</span></div>
          <div className="issue-list">
            {punct.map((issue, i) => (
              <FmtItem key={i} issue={issue} kind="punct" />
            ))}
          </div>
        </>
      )}
    </>
  )
}

function FmtItem({ issue, kind }: { issue: FormattingIssue; kind: 'reversal' | 'punct' }) {
  return (
    <div className="fmt-item">
      <span className={`fmt-badge ${kind}`}>
        {kind === 'reversal' ? 'Word Order' : 'Punctuation'}
      </span>
      <div className="fmt-cmp">
        <div className="fmt-side">
          <div className="fmt-side-label">GT</div>
          <div className="fmt-text gt" dir="auto">{issue.gt_text ?? issue.ngram ?? ''}</div>
        </div>
        <div className="fmt-cmp-arrow">→</div>
        <div className="fmt-side">
          <div className="fmt-side-label">Parser</div>
          <div className="fmt-text parser" dir="auto">{issue.parser_text ?? ''}</div>
        </div>
      </div>
      {issue.evidence && (
        <div className="fmt-evidence">
          {issue.evidence}
          {issue.confidence && (
            <span className={`conf-badge ${issue.confidence}`}>{issue.confidence}</span>
          )}
        </div>
      )}
    </div>
  )
}

function UnclassifiedBody({ ngrams }: { ngrams: string[] }) {
  return (
    <div className="ngram-cloud">
      {ngrams.map((ng, i) => (
        <span key={i} className="tag tag-ngram" dir="auto">{ng}</span>
      ))}
    </div>
  )
}

/* ── Per-document cards ──────────────────────────────────────── */

export function DiagnosticCardsForDoc({ doc }: { doc: DiagnosticDocument }) {
  const dp = doc.detected_problems
  return (
    <>
      <DiagCard color="var(--c-missing)" count={dp.MISSING_BLOCK_PARSE.count}
                name="Missing Block Parse"
                desc="Blocks where ≤10% of GT content was found in parser output"
                delaySec={0}>
        <MissingBlocksBody blocks={dp.MISSING_BLOCK_PARSE.blocks_number} />
      </DiagCard>
      <DiagCard color="var(--c-ocr)" count={dp.OCR_SPLIT.count}
                name="OCR Split"
                desc="GT words split into two consecutive fragments by the parser"
                delaySec={0.05}>
        <OcrSplitsBody issues={dp.OCR_SPLIT.issues} />
      </DiagCard>
      <DiagCard color="var(--c-merged)" count={dp.MERGED_WORDS.count}
                name="Merged Words"
                desc="Two adjacent GT words concatenated into one token"
                delaySec={0.10}>
        <MergedWordsBody issues={dp.MERGED_WORDS.issues} />
      </DiagCard>
      <DiagCard color="var(--c-format)" count={dp.FORMATTING_ISSUES.count}
                name="Formatting Issues"
                desc="Word order reversals and misplaced punctuation tokens"
                delaySec={0.15}>
        <FormattingBody data={dp.FORMATTING_ISSUES} />
      </DiagCard>
      <DiagCard color="var(--c-unclass)" count={dp.UNCLASSIFIED.count}
                name="Unclassified"
                desc="Missing ngrams that no detector could explain"
                delaySec={0.20}>
        <UnclassifiedBody ngrams={dp.UNCLASSIFIED.ngrams} />
      </DiagCard>
    </>
  )
}

/* ── Aggregated cards (across all docs, with per-doc badges) ─── */

interface AggCounts {
  MISSING_BLOCK_PARSE: number
  OCR_SPLIT:           number
  MERGED_WORDS:        number
  FORMATTING_ISSUES:   number
  UNCLASSIFIED:        number
}

interface BadgedIssue<T> { value: T; badge: string }

function DocBadge({ name }: { name: string }) {
  return <span className="doc-badge">{trunc(name, 20)}</span>
}

export function DiagnosticCardsAggregated({ docs, counts }: {
  docs:   DiagnosticDocument[]
  counts: AggCounts
}) {
  const allMissing:    BadgedIssue<number>[]          = []
  const allOcr:        BadgedIssue<OcrSplitIssue>[]   = []
  const allMerged:     BadgedIssue<MergedWordIssue>[] = []
  const allReversals:  BadgedIssue<FormattingIssue>[] = []
  const allPunct:      BadgedIssue<FormattingIssue>[] = []

  docs.forEach(doc => {
    const dp = doc.detected_problems
    const badge = doc.doc_name
    ;(dp.MISSING_BLOCK_PARSE?.blocks_number ?? []).forEach(bn =>
      allMissing.push({ value: bn, badge }),
    )
    ;(dp.OCR_SPLIT?.issues ?? []).forEach(issue =>
      allOcr.push({ value: issue, badge }),
    )
    ;(dp.MERGED_WORDS?.issues ?? []).forEach(issue =>
      allMerged.push({ value: issue, badge }),
    )
    ;(dp.FORMATTING_ISSUES?.WORD_ORDER_REVERSAL?.issues ?? []).forEach(issue =>
      allReversals.push({ value: issue, badge }),
    )
    ;(dp.FORMATTING_ISSUES?.MISPLACED_PUNCTUATION?.issues ?? []).forEach(issue =>
      allPunct.push({ value: issue, badge }),
    )
  })

  return (
    <>
      <DiagCard color="var(--c-missing)" count={counts.MISSING_BLOCK_PARSE}
                name="Missing Block Parse"
                desc="Blocks where ≤10% of GT content was found — all files"
                delaySec={0}>
        <div className="block-pills">
          {allMissing.map(({ value, badge }, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <DocBadge name={badge} />
              <span className="block-pill">Block {value}</span>
            </div>
          ))}
        </div>
      </DiagCard>

      <DiagCard color="var(--c-ocr)" count={counts.OCR_SPLIT}
                name="OCR Split"
                desc="GT words split into fragments by the parser — all files"
                delaySec={0.05}>
        <div className="issue-list">
          {allOcr.map(({ value: issue, badge }, i) => {
            const word  = issue.original_word ?? issue.word ?? '?'
            const frags = issue.fragments_in_parser ?? issue.fragments ?? []
            return (
              <div key={i} className="ocr-item">
                <DocBadge name={badge} />
                <span className="ocr-word" dir="auto">{word}</span>
                <span className="arr">→</span>
                <div className="ocr-frags">
                  {frags.map((f, j) => (
                    <span key={j} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                      {j > 0 && <span className="chip-plus">+</span>}
                      <span className="frag-chip" dir="auto">{f}</span>
                    </span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </DiagCard>

      <DiagCard color="var(--c-merged)" count={counts.MERGED_WORDS}
                name="Merged Words"
                desc="Two adjacent GT words concatenated into one token — all files"
                delaySec={0.10}>
        <div className="issue-list">
          {allMerged.map(({ value: issue, badge }, i) => (
            <div key={i} className="merge-item">
              <DocBadge name={badge} />
              <div className="orig-chips">
                {(issue.original ?? []).map((p, j) => (
                  <span key={j} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                    {j > 0 && <span className="chip-plus">+</span>}
                    <span className="orig-chip" dir="auto">{p}</span>
                  </span>
                ))}
              </div>
              <span className="arr">→</span>
              <span className="merged-chip" dir="auto">{issue.merged_word}</span>
            </div>
          ))}
        </div>
      </DiagCard>

      <DiagCard color="var(--c-format)" count={counts.FORMATTING_ISSUES}
                name="Formatting Issues"
                desc="Word order reversals and misplaced punctuation — all files"
                delaySec={0.15}>
        {allReversals.length > 0 && (
          <>
            <div className="sub-hdr">Word Order Reversals <span>{allReversals.length}</span></div>
            <div className="issue-list">
              {allReversals.map(({ value, badge }, i) => (
                <AggFmtItem key={i} issue={value} badge={badge} kind="reversal" />
              ))}
            </div>
          </>
        )}
        {allPunct.length > 0 && (
          <>
            <div className="sub-hdr">Misplaced Punctuation <span>{allPunct.length}</span></div>
            <div className="issue-list">
              {allPunct.map(({ value, badge }, i) => (
                <AggFmtItem key={i} issue={value} badge={badge} kind="punct" />
              ))}
            </div>
          </>
        )}
      </DiagCard>

      <DiagCard color="var(--c-unclass)" count={counts.UNCLASSIFIED}
                name="Unclassified"
                desc="Missing ngrams that no detector could explain — all files"
                delaySec={0.20}>
        <div style={{ paddingTop: 12 }}>
          {docs.map(doc => {
            const ngrams = doc.detected_problems.UNCLASSIFIED?.ngrams ?? []
            if (!ngrams.length) return null
            return (
              <div key={doc.doc_name} style={{ marginBottom: 12 }}>
                <div style={{
                  fontSize: '0.68rem',
                  color: 'var(--text-3)',
                  marginBottom: 6,
                  fontFamily: 'var(--f-mono)',
                }}>
                  {doc.doc_name}
                </div>
                <div className="ngram-cloud">
                  {ngrams.map((ng, i) => (
                    <span key={i} className="tag tag-ngram" dir="auto">{ng}</span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </DiagCard>
    </>
  )
}

function AggFmtItem({ issue, badge, kind }: {
  issue: FormattingIssue
  badge: string
  kind:  'reversal' | 'punct'
}) {
  return (
    <div className="fmt-item">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span className={`fmt-badge ${kind}`}>
          {kind === 'reversal' ? 'Word Order' : 'Punctuation'}
        </span>
        <DocBadge name={badge} />
      </div>
      <div className="fmt-cmp">
        <div className="fmt-side">
          <div className="fmt-side-label">GT</div>
          <div className="fmt-text gt" dir="auto">{issue.gt_text ?? issue.ngram ?? ''}</div>
        </div>
        <div className="fmt-cmp-arrow">→</div>
        <div className="fmt-side">
          <div className="fmt-side-label">Parser</div>
          <div className="fmt-text parser" dir="auto">{issue.parser_text ?? ''}</div>
        </div>
      </div>
      {issue.evidence && (
        <div className="fmt-evidence">
          {issue.evidence}
          {issue.confidence && (
            <span className={`conf-badge ${issue.confidence}`}>{issue.confidence}</span>
          )}
        </div>
      )}
    </div>
  )
}
