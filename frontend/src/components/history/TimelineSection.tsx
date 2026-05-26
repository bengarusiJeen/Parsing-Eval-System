/* TimelineSection — composes Controls + WarningBanner + Chart + StatusBlock.
   Owns selection state and the fetch. Fetches one timeline per selected parser
   in parallel and combines results into a multi-series chart.

   The corpus dropdown's option list is loaded lazily the first time the user
   picks `mode === 'corpus'`. It re-loads on each mount of this component
   (i.e. each time History → Timeline is re-entered) so newly created corpora
   from the Corpora tab appear without a hard refresh. */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { listCorpora } from '../../api/corporaApi'
import {
  fetchCorpusTimeline,
  fetchFilesTimeline,
  fetchOverallTimeline,
  fetchParserTimeline,
} from '../../api/historyApi'
import { ApiError } from '../../api/client'
import { useAppState } from '../../state/AppContext'
import { parserLabel } from '../../types/parser'
import type { Corpus } from '../../types/corpus'
import type {
  OverallTimelineResponse,
  TimelineMetric,
  TimelineMode,
  TimelineResponse,
} from '../../types/history'

import type { ChartPoint, ChartSeries } from './TimelineChart'
import { TimelineChart, colorForParser } from './TimelineChart'
import { TimelineControls } from './TimelineControls'
import { TimelineWarningBanner } from './TimelineWarningBanner'
import { StatusBlock } from './StatusBlock'

type StatusState = 'loading' | 'error' | 'empty' | null

function adaptTimeline(
  resp: TimelineResponse,
  metric: TimelineMetric,
): ChartPoint[] {
  return resp.points.map(p => {
    const raw =
      metric === 'avg_score' ? p.avg_score :
      metric === 'coverage'  ? p.coverage  :
                               p.noise
    return {
      x: new Date(p.started_at),
      y: raw,
      runId: p.run_id,
      fileSetChanged: p.file_set_changed,
    }
  })
}

function adaptOverall(resp: OverallTimelineResponse): {
  points: ChartPoint[]; firstWarning: string | null
} {
  let firstWarning: string | null = null
  const points: ChartPoint[] = resp.points.map(p => {
    if (firstWarning == null && p.warning) firstWarning = p.warning
    return {
      x: new Date(p.started_at),
      y: p.overall_score,
      runId: p.run_id,
      fileSetChanged: false,
      warning: p.warning,
    }
  })
  return { points, firstWarning }
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

export function TimelineSection() {
  const { availableFiles } = useAppState()

  // Selection state (local to this section)
  const [selectedParsers, setSelectedParsers] = useState<Set<string>>(
    () => new Set(['base_text_parser']),
  )
  const [metric, setMetric] = useState<TimelineMetric>('avg_score')
  const [mode, setMode] = useState<TimelineMode>('all')
  const [limit, setLimit] = useState<number>(7)
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [selectedCorpusId, setSelectedCorpusId] = useState<number | null>(null)

  // Corpora cache (lazy-loaded on entering 'corpus' mode; refreshed on remount)
  const [corpora, setCorpora] = useState<Corpus[]>([])
  const [corporaLoading, setCorporaLoading] = useState(false)
  const [corporaError, setCorporaError] = useState<string | null>(null)
  const corporaLoadedRef = useRef(false)

  // Data state
  const [series, setSeries] = useState<ChartSeries[]>([])
  const [warning, setWarning] = useState<string | null>(null)
  const [status, setStatus] = useState<StatusState>('loading')
  const [errorMsg, setErrorMsg] = useState<string>('')

  const effectiveMetric: TimelineMetric = mode === 'overall' ? 'avg_score' : metric

  // Toggle a parser on/off; require at least one selected.
  const toggleParser = useCallback((id: string) => {
    setSelectedParsers(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        if (next.size > 1) next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  // Lazy corpora load on entering 'corpus' mode for the first time per mount.
  useEffect(() => {
    if (mode !== 'corpus' || corporaLoadedRef.current) return
    corporaLoadedRef.current = true
    let cancelled = false
    setCorporaLoading(true)
    setCorporaError(null)
    listCorpora(false)
      .then(list => { if (!cancelled) setCorpora(list) })
      .catch(err => { if (!cancelled) setCorporaError(friendlyApiError(err)) })
      .finally(() => { if (!cancelled) setCorporaLoading(false) })
    return () => { cancelled = true }
  }, [mode])

  const toggleFile = useCallback((name: string) => {
    setSelectedFiles(prev => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }, [])

  const filesKey = useMemo(
    () => Array.from(selectedFiles).sort().join('|'),
    [selectedFiles],
  )
  const parsersKey = useMemo(
    () => Array.from(selectedParsers).sort().join('|'),
    [selectedParsers],
  )

  // Main fetch effect — runs in parallel across selected parsers.
  useEffect(() => {
    let cancelled = false

    const parsers = Array.from(selectedParsers)
    if (parsers.length === 0) {
      setSeries([]); setWarning(null); setStatus('empty')
      setErrorMsg(''); return
    }

    const needsCorpus = mode === 'corpus' && selectedCorpusId == null
    const needsFiles  = mode === 'files'  && selectedFiles.size === 0

    if (needsCorpus || needsFiles) {
      setSeries([]); setWarning(null); setStatus('empty')
      setErrorMsg(''); return
    }

    setStatus('loading')
    setErrorMsg('')
    setWarning(null)

    const fetchOne = async (parser: string): Promise<ChartSeries> => {
      const common = {
        parserId:    parser,
        parserLabel: parserLabel(parser),
        color:       colorForParser(parser),
      }
      if (mode === 'all') {
        const resp = await fetchParserTimeline(parser, limit)
        return { ...common, points: adaptTimeline(resp, effectiveMetric) }
      }
      if (mode === 'files') {
        const files = Array.from(selectedFiles)
        const resp = await fetchFilesTimeline(parser, files, limit)
        return { ...common, points: adaptTimeline(resp, effectiveMetric) }
      }
      if (mode === 'corpus') {
        const resp = await fetchCorpusTimeline(parser, selectedCorpusId!, limit)
        return { ...common, points: adaptTimeline(resp, effectiveMetric) }
      }
      // overall
      const resp = await fetchOverallTimeline(parser, limit)
      const { points, firstWarning } = adaptOverall(resp)
      // stash the warning on the series object via a sentinel property
      return Object.assign({ ...common, points }, { _warning: firstWarning })
    }

    Promise.all(parsers.map(fetchOne))
      .then(results => {
        if (cancelled) return
        setSeries(results)

        // overall mode: ratios are global so all parsers return the same
        // warning text; surface the first non-null one.
        if (mode === 'overall') {
          const w = results
            .map(r => (r as ChartSeries & { _warning?: string | null })._warning)
            .find(Boolean) ?? null
          setWarning(w)
        }

        const totalPoints = results.reduce((n, s) => n + s.points.length, 0)
        setStatus(totalPoints === 0 ? 'empty' : null)
      })
      .catch(err => {
        if (cancelled) return
        setSeries([])
        setWarning(null)
        setErrorMsg(friendlyApiError(err))
        setStatus('error')
      })

    return () => { cancelled = true }
  }, [
    parsersKey, selectedParsers,
    mode, limit, filesKey, selectedFiles,
    selectedCorpusId, effectiveMetric,
  ])

  const emptyMessage =
    selectedParsers.size === 0
      ? 'Pick at least one parser to see the timeline.'
      : mode === 'overall'
        ? 'No active corpora yet. Create a corpus in the Corpora tab and assign files to see the overall timeline.'
        : mode === 'files' && selectedFiles.size === 0
          ? 'Pick one or more files to see the timeline.'
          : mode === 'corpus' && selectedCorpusId == null
            ? 'Pick a corpus to see the timeline.'
            : 'No history yet. Run an evaluation first.'

  return (
    <section className="report-section">
      <div className="sec-hdr">
        <h3>Timeline</h3>
      </div>

      <TimelineControls
        selectedParsers={selectedParsers}
        onToggleParser={toggleParser}
        metric={metric}
        onMetricChange={setMetric}
        mode={mode}
        onModeChange={setMode}
        limit={limit}
        onLimitChange={setLimit}
        availableFiles={availableFiles}
        selectedFiles={selectedFiles}
        onToggleFile={toggleFile}
        corpora={corpora}
        corporaLoading={corporaLoading}
        corporaError={corporaError}
        selectedCorpusId={selectedCorpusId}
        onCorpusChange={setSelectedCorpusId}
      />

      {mode === 'overall' && <TimelineWarningBanner message={warning} />}

      {status === null && (
        <TimelineChart series={series} metric={effectiveMetric} />
      )}
      <StatusBlock
        state={status}
        message={
          status === 'error'   ? errorMsg :
          status === 'empty'   ? emptyMessage :
          status === 'loading' ? 'Loading timeline…' : undefined
        }
      />
    </section>
  )
}
