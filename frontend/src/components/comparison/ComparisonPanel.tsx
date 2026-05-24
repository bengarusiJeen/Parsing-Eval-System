/* ComparisonPanel — pure display layer for the Compare tab.
 *
 * All data comes from backend endpoints:
 *   GET  /api/comparison/info   → available parsers + docs (filter UI)
 *   POST /api/comparison/filter → ranked scores
 *
 * The panel reads only `status` from AppContext so it knows when new
 * results are ready to fetch.  No evaluation data flows from the
 * frontend to the backend — storage and computation stay in the backend.
 */

import { useEffect, useState } from 'react'

import { fetchComparison, fetchComparisonInfo } from '../../api/comparisonApi'
import { useAppState } from '../../state/AppContext'
import type { ComparisonResult } from '../../types/comparison'
import { ComparisonFilters } from './ComparisonFilters'
import { ComparisonTable } from './ComparisonTable'

export function ComparisonPanel() {
  const { status } = useAppState()   // only need to know when results are ready

  const [runParsers,    setRunParsers]    = useState<string[]>([])
  const [availableDocs, setAvailableDocs] = useState<string[]>([])
  const [parserSel,     setParserSel]     = useState<Set<string>>(new Set())
  const [docSel,        setDocSel]        = useState<Set<string>>(new Set())
  const [result,        setResult]        = useState<ComparisonResult | null>(null)
  const [err,           setErr]           = useState<string | null>(null)

  /* Fetch available parsers + docs from the backend whenever results become ready.
     Keeps old data visible while a new run is in progress (status === 'loading'). */
  useEffect(() => {
    if (status !== 'ready') return

    fetchComparisonInfo()
      .then(info => {
        setRunParsers(info.parsers)
        setAvailableDocs(info.docs)
        setParserSel(new Set(info.parsers))
        setDocSel(new Set(info.docs))
      })
      .catch(() => {
        setRunParsers([])
        setAvailableDocs([])
      })
  }, [status])

  /* Fetch comparison scores whenever the filter selection changes. */
  useEffect(() => {
    if (parserSel.size === 0) {
      setErr('Select at least one parser.')
      setResult(null)
      return
    }
    if (runParsers.length === 0 || availableDocs.length === 0) {
      setErr('Run an evaluation first to see comparisons.')
      setResult(null)
      return
    }

    let cancelled = false
    setErr(null)
    fetchComparison({ parsers: [...parserSel], docs: [...docSel] })
      .then(res => { if (!cancelled) setResult(res) })
      .catch(e => {
        if (cancelled) return
        const body = (e as { body?: { error?: string } })?.body
        setErr(body?.error ?? `Network error: ${String(e)}`)
        setResult(null)
      })
    return () => { cancelled = true }
  }, [parserSel, docSel, runParsers.length, availableDocs.length])

  const toggleSet = (setter: React.Dispatch<React.SetStateAction<Set<string>>>) =>
    (id: string) => setter(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })

  return (
    <div id="comparison-panel">
      <div>
        <div className="cmp-header">
          <div className="cmp-title">Parser Comparison</div>
          <div className="cmp-sub">Weighted pooled scores across selected documents</div>
        </div>
      </div>

      <ComparisonFilters
        availableParsers={runParsers}
        availableDocs={availableDocs}
        selectedParsers={parserSel}
        selectedDocs={docSel}
        toggleParser={toggleSet(setParserSel)}
        toggleDoc={toggleSet(setDocSel)}
      />

      <ComparisonTable
        title="Raw Parser Output"
        subBadge="Before Postprocessing"
        scores={result?.scores ?? null}
        rankAttr="rank_raw"
        covAttr="weighted_coverage_raw"
        noiseAttr="weighted_noise_raw"
        errorText={err}
      />

      <ComparisonTable
        title="Post-Processed Output"
        subBadge="After Postprocessing"
        scores={result?.scores ?? null}
        rankAttr="rank_post"
        covAttr="weighted_coverage_post"
        noiseAttr="weighted_noise_post"
        errorText={err}
      />
    </div>
  )
}
