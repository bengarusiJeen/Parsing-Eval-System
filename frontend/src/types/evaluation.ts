/* evaluation.ts — request + response types for /api/evaluate and /api/results */

import type { GeneralReport, DiagnosticReport } from './reports'

export interface EvaluateRequest {
  selected: string[]
  parsers: string[]
}

/* Single-parser evaluation result (also used per-parser in multi-parser runs) */
export interface SingleParserResult {
  status: 'ok' | 'error'
  returncode?: number
  stdout?: string
  stderr?: string
  error?: string
  general:       GeneralReport      | null
  diagnostic:    DiagnosticReport   | null
  general_pp:    GeneralReport      | null
  diagnostic_pp: DiagnosticReport   | null
}

/* Multi-parser response wrapper */
export interface MultiParserResponse {
  multi_parser: true
  parsers: Record<string, SingleParserResult>
}

export type EvaluateResponse = SingleParserResult | MultiParserResponse

export function isMultiParser(r: EvaluateResponse): r is MultiParserResponse {
  return (r as MultiParserResponse).multi_parser === true
}

/* /api/results response — backend returns the same shape as SingleParserResult
   when results exist, or {status:'no_results'} when none do. */
export type ResultsResponse =
  | SingleParserResult
  | { status: 'no_results' }
