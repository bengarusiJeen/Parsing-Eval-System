/* ComparisonPanel — top-level layout for the Compare tab: filters + raw + PP tables */

import { useEffect, useMemo, useState } from 'react'

import { fetchComparison } from '../../api/comparisonApi'
import { useAppState } from '../../state/AppContext'
import type { ComparisonResult, InlineParserReports } from '../../types/comparison'
import { ComparisonFilters } from './ComparisonFilters'
import { ComparisonTable } from './ComparisonTable'

export function ComparisonPanel() {
  const {
    selectedParsers,
    parserResults,
    general,
    general_pp,
  } = useAppState()

  /* Available parsers come from the latest run: */
  const runParsers = useMemo(() => {
    if (Object.keys(parserResults).length > 0) return Object.keys(parserResults)
    return [...selectedParsers]
  }, [parserResults, selectedParsers])

  /* Build inline reports map for the comparison endpoint */
  const reportsMap = useMemo<InlineParserReports>(() => {
    if (Object.keys(parserResults).length > 0) {
      const out: InlineParserReports = {}
      for (const [pid, d] of Object.entries(parserResults)) {
        out[pid] = {
          general:    d.general ?? null,
          general_pp: d.general_pp ?? null,
        }
      }
      return out
    }
    if (runParsers.length === 1 && general) {
      return {
        [runParsers[0]]: { general, general_pp: general_pp ?? null },
      }
    }
    return {}
  }, [parserResults, runParsers, general, general_pp])

  /* Derive available docs */
  const availableDocs = useMemo(() => {
    const firstReport = Object.values(reportsMap)[0]
    return (firstReport?.general?.documents ?? []).map(d => d.doc_name).filter(Boolean)
  }, [reportsMap])

  /* Filter selections */
  const [parserSel, setParserSel] = useState<Set<string>>(() => new Set(runParsers))
  const [docSel,    setDocSel]    = useState<Set<string>>(() => new Set(availableDocs))

  /* Reset selections when the underlying data changes */
  useEffect(() => { setParserSel(new Set(runParsers)) },    [runParsers])
  useEffect(() => { setDocSel(new Set(availableDocs)) },    [availableDocs])

  /* Result + loading + error */
  const [result, setResult] = useState<ComparisonResult | null>(null)
  const [err,    setErr]    = useState<string | null>(null)

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
    fetchComparison({
      parsers: [...parserSel],
      docs:    [...docSel],
      parser_reports: Object.keys(reportsMap).length ? reportsMap : null,
    })
      .then(res => { if (!cancelled) setResult(res) })
      .catch(e => {
        if (cancelled) return
        const body = (e as { body?: { error?: string } })?.body
        setErr(body?.error ?? `Network error: ${String(e)}`)
        setResult(null)
      })
    return () => { cancelled = true }
  }, [parserSel, docSel, reportsMap, runParsers.length, availableDocs.length])

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
