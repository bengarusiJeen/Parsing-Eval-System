/* history.ts — types for /api/history/* responses (Stage 1 + 2). */

export interface RunSummary {
  id: number
  run_type: string
  status: 'running' | 'completed' | 'partial' | 'failed' | string
  started_at: string         // ISO 8601
  finished_at: string | null
  parsers: string[]
  files_count: number
}

export interface ResultRow {
  parser_name: string
  file_name: string
  coverage_checked: number
  coverage_failed: number
  coverage_rate: number
  noise_checked: number
  noise_failed: number
  noise_rate: number
  avg_score: number
  gt_word_count: number
  parser_word_count: number
  diagnostics_json: Record<string, unknown> | null
}

export interface RunDetail extends RunSummary {
  selected_files: string[]
  results: ResultRow[]
}

export interface TimelinePoint {
  run_id: number
  started_at: string
  parser_name: string
  coverage: number | null
  noise: number | null
  avg_score: number | null
  doc_count: number
  file_set_changed: boolean
}

export interface TimelineFilterEcho {
  parser: string
  files: string[] | null
}

export interface TimelineResponse {
  points: TimelinePoint[]
  filter_echo: TimelineFilterEcho
}

export interface OverallTimelinePoint {
  run_id: number
  started_at: string
  overall_score: number | null
  contributing_corpora: number
  ratios_sum: number
  normalization_applied: boolean
  warning: string | null
  per_corpus: Record<string, number | null>
}

export interface OverallTimelineResponse {
  points: OverallTimelinePoint[]
  parser: string
}

export type TimelineMode = 'all' | 'files' | 'corpus' | 'overall'
export type TimelineMetric = 'avg_score' | 'coverage' | 'noise'
