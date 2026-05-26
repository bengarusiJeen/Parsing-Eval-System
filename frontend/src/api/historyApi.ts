/* historyApi.ts — read endpoints for /api/history/*. */

import { apiGet } from './client'
import type {
  OverallTimelineResponse,
  RunDetail,
  RunSummary,
  TimelineResponse,
} from '../types/history'

export const fetchRuns = (limit = 7) =>
  apiGet<RunSummary[]>(`/api/history/runs?limit=${limit}`)

export const fetchRunDetail = (id: number, includeDiagnostics = false) =>
  apiGet<RunDetail>(
    `/api/history/runs/${id}?include_diagnostics=${includeDiagnostics}`,
  )

export const fetchParserTimeline = (parser: string, limit = 7) =>
  apiGet<TimelineResponse>(
    `/api/history/timeline?parser=${encodeURIComponent(parser)}&limit=${limit}`,
  )

export const fetchFilesTimeline = (parser: string, files: string[], limit = 7) =>
  apiGet<TimelineResponse>(
    `/api/history/timeline?parser=${encodeURIComponent(parser)}` +
    `&files=${files.map(encodeURIComponent).join(',')}&limit=${limit}`,
  )

export const fetchCorpusTimeline = (parser: string, corpusId: number, limit = 7) =>
  apiGet<TimelineResponse>(
    `/api/history/timeline?parser=${encodeURIComponent(parser)}` +
    `&corpus_id=${corpusId}&limit=${limit}`,
  )

export const fetchOverallTimeline = (parser: string, limit = 7) =>
  apiGet<OverallTimelineResponse>(
    `/api/history/timeline/overall?parser=${encodeURIComponent(parser)}&limit=${limit}`,
  )
