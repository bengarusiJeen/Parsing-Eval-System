/* AppContext.tsx — single source of truth for cross-page state.
   Mirrors the legacy global `S` object: results data, active nav, active doc, etc. */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import type { FileEntry } from '../types/file'
import type {
  EvaluateResponse,
  SingleParserResult,
} from '../types/evaluation'
import { isMultiParser } from '../types/evaluation'
import type {
  GeneralReport,
  DiagnosticReport,
} from '../types/reports'

/* ── State shape ─────────────────────────────────────────────── */

export type AppStatus = 'idle' | 'loading' | 'ready' | 'error'

export type NavView    = 'setup' | 'results' | 'comparison' | 'history' | 'corpora'
export type ReportType = 'general' | 'postprocessing' | 'stream'
export type SummaryTab = 'files' | 'global'

/* activeDoc is either a numeric index into the document list, or 'summary' */
export type ActiveDoc = number | 'summary'

export interface AppState {
  /* status */
  status: AppStatus
  errorLog: string
  stdoutLog: string

  /* navigation */
  activeNav: NavView
  activeDoc: ActiveDoc
  activeReport: ReportType
  activeSummaryTab: SummaryTab

  /* setup state */
  availableFiles: FileEntry[]
  selectedFiles: Set<string>
  selectedParsers: Set<string>

  /* results */
  general:       GeneralReport    | null
  diagnostic:    DiagnosticReport | null
  general_pp:    GeneralReport    | null
  diagnostic_pp: DiagnosticReport | null

  /* multi-parser */
  parserResults: Record<string, SingleParserResult>  // empty for single-parser runs
  activeParser:  string | null                       // null for single-parser
}

/* ── Actions ─────────────────────────────────────────────────── */

export interface AppActions {
  /* setup */
  setAvailableFiles: (files: FileEntry[]) => void
  toggleFile: (name: string) => void
  selectAllFiles: () => void
  clearFiles: () => void
  toggleParser: (id: string) => void

  /* navigation */
  switchNav: (nav: NavView) => void
  selectDoc: (idx: ActiveDoc) => void
  setReport: (t: ReportType) => void
  setSummaryTab: (t: SummaryTab) => void

  /* evaluation lifecycle */
  startEvaluation: () => void
  loadResults: (data: SingleParserResult) => void
  loadMultiParserResults: (data: { parsers: Record<string, SingleParserResult> }) => void
  switchParserTab: (parserId: string) => void
  showError: (msg: string) => void
  setStdoutLog: (text: string) => void
  applyResponse: (data: EvaluateResponse) => void
}

/* ── Context ─────────────────────────────────────────────────── */

const Ctx = createContext<(AppState & AppActions) | null>(null)

export function useAppState(): AppState & AppActions {
  const v = useContext(Ctx)
  if (!v) throw new Error('useAppState must be used inside <AppProvider>')
  return v
}

/* ── Provider ────────────────────────────────────────────────── */

function initialState(): AppState {
  return {
    status:   'idle',
    errorLog: '',
    stdoutLog: '',

    activeNav:        'setup',
    activeDoc:        'summary',
    activeReport:     'general',
    activeSummaryTab: 'files',

    availableFiles:  [],
    selectedFiles:   new Set<string>(),
    selectedParsers: new Set<string>(['document_intelligence']),

    general:       null,
    diagnostic:    null,
    general_pp:    null,
    diagnostic_pp: null,

    parserResults: {},
    activeParser:  null,
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(initialState)

  const patch = useCallback((p: Partial<AppState>) => {
    setState(prev => ({ ...prev, ...p }))
  }, [])

  /* ── setup actions ───────────────────────────────────────── */

  const setAvailableFiles = useCallback((files: FileEntry[]) => {
    patch({ availableFiles: files })
  }, [patch])

  const toggleFile = useCallback((name: string) => {
    setState(prev => {
      const next = new Set(prev.selectedFiles)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return { ...prev, selectedFiles: next }
    })
  }, [])

  const selectAllFiles = useCallback(() => {
    setState(prev => ({
      ...prev,
      selectedFiles: new Set(prev.availableFiles.map(f => f.name)),
    }))
  }, [])

  const clearFiles = useCallback(() => {
    setState(prev => ({ ...prev, selectedFiles: new Set() }))
  }, [])

  const toggleParser = useCallback((id: string) => {
    setState(prev => {
      const next = new Set(prev.selectedParsers)
      if (next.has(id)) {
        // Keep at least one parser selected
        if (next.size > 1) next.delete(id)
      } else {
        next.add(id)
      }
      return { ...prev, selectedParsers: next }
    })
  }, [])

  /* ── navigation actions ──────────────────────────────────── */

  const switchNav = useCallback((nav: NavView) => {
    patch({ activeNav: nav })
  }, [patch])

  const selectDoc = useCallback((idx: ActiveDoc) => {
    setState(prev => {
      if (idx === 'summary') {
        return {
          ...prev,
          activeDoc:        'summary',
          activeReport:     'general',
          activeSummaryTab: 'files',
        }
      }
      return { ...prev, activeDoc: idx }
    })
  }, [])

  const setReport = useCallback((t: ReportType) => {
    patch({ activeReport: t })
  }, [patch])

  const setSummaryTab = useCallback((t: SummaryTab) => {
    patch({ activeSummaryTab: t })
  }, [patch])

  /* ── evaluation actions ──────────────────────────────────── */

  const startEvaluation = useCallback(() => {
    patch({
      status: 'loading',
      errorLog: '',
      stdoutLog: '',
      activeNav: 'results',
    })
  }, [patch])

  const setStdoutLog = useCallback((text: string) => {
    patch({ stdoutLog: text })
  }, [patch])

  const loadResults = useCallback((data: SingleParserResult) => {
    patch({
      parserResults: {},
      activeParser:  null,
      general:       data.general,
      diagnostic:    data.diagnostic,
      general_pp:    data.general_pp    ?? null,
      diagnostic_pp: data.diagnostic_pp ?? null,
      activeDoc:     'summary',
      activeReport:  'general',
      status:        'ready',
    })
  }, [patch])

  const showError = useCallback((msg: string) => {
    patch({ status: 'error', errorLog: msg })
  }, [patch])

  const loadMultiParserResults = useCallback(
    (data: { parsers: Record<string, SingleParserResult> }) => {
      const firstOkId = Object.keys(data.parsers).find(
        id => data.parsers[id].status === 'ok',
      )

      if (!firstOkId) {
        const errLines = Object.entries(data.parsers)
          .map(([id, d]) => `${id}:\n${d.stderr || d.error || 'Unknown error'}`)
          .join('\n\n')
        patch({
          status:        'error',
          errorLog:      'All parsers failed:\n\n' + errLines,
          parserResults: data.parsers,
        })
        return
      }

      const d = data.parsers[firstOkId]
      patch({
        parserResults: data.parsers,
        activeParser:  firstOkId,
        general:       d.general,
        diagnostic:    d.diagnostic,
        general_pp:    d.general_pp    ?? null,
        diagnostic_pp: d.diagnostic_pp ?? null,
        activeDoc:     'summary',
        activeReport:  'general',
        status:        'ready',
      })
    },
    [patch],
  )

  const switchParserTab = useCallback((parserId: string) => {
    setState(prev => {
      const d = prev.parserResults[parserId]
      if (d && d.status === 'ok') {
        return {
          ...prev,
          activeParser:  parserId,
          general:       d.general,
          diagnostic:    d.diagnostic,
          general_pp:    d.general_pp    ?? null,
          diagnostic_pp: d.diagnostic_pp ?? null,
          activeDoc:     'summary',
          activeReport:  'general',
        }
      }
      return {
        ...prev,
        activeParser:  parserId,
        general:       null,
        diagnostic:    null,
        general_pp:    null,
        diagnostic_pp: null,
        activeDoc:     'summary',
        activeReport:  'general',
      }
    })
  }, [])

  const applyResponse = useCallback((data: EvaluateResponse) => {
    if (isMultiParser(data)) {
      const firstOk = Object.values(data.parsers).find(d => d.stdout)
      if (firstOk?.stdout) setStdoutLog(firstOk.stdout)
      loadMultiParserResults(data)
    } else {
      if (data.stdout) setStdoutLog(data.stdout)
      if (data.status === 'ok' && data.general) {
        loadResults(data)
      } else if (data.status === 'ok') {
        showError(
          'Evaluation produced no results.\nCheck that the selected files are valid and the parser service is running.\n\n' +
            (data.stderr || ''),
        )
      } else {
        showError(
          data.stderr || data.error || `Exit code ${data.returncode ?? '?'}`,
        )
      }
    }
  }, [loadMultiParserResults, loadResults, setStdoutLog, showError])

  const value = useMemo<AppState & AppActions>(() => ({
    ...state,
    setAvailableFiles,
    toggleFile,
    selectAllFiles,
    clearFiles,
    toggleParser,
    switchNav,
    selectDoc,
    setReport,
    setSummaryTab,
    startEvaluation,
    loadResults,
    loadMultiParserResults,
    switchParserTab,
    showError,
    setStdoutLog,
    applyResponse,
  }), [
    state,
    setAvailableFiles, toggleFile, selectAllFiles, clearFiles, toggleParser,
    switchNav, selectDoc, setReport, setSummaryTab,
    startEvaluation, loadResults, loadMultiParserResults, switchParserTab,
    showError, setStdoutLog, applyResponse,
  ])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
