/* comparison.ts — types for /api/comparison and /api/comparison/filter */

import type { GeneralReport } from './reports'

export interface ParserDocumentScore {
  parser_name: string
  doc_name: string
  coverage_checked: number
  coverage_failed: number
  noise_checked: number
  noise_failed: number
  post_coverage_checked: number
  post_coverage_failed: number
  post_noise_checked: number
  post_noise_failed: number
}

export interface ParserCorpusScore {
  parser_name: string
  docs: ParserDocumentScore[]
  weighted_coverage_raw:  number
  weighted_noise_raw:     number
  weighted_coverage_post: number
  weighted_noise_post:    number
  rank_raw:  number
  rank_post: number
}

export interface ComparisonResult {
  selected_docs: string[]
  parsers: string[]
  scores: ParserCorpusScore[]
}

export interface InlineParserReports {
  [parserId: string]: {
    general:    GeneralReport | null
    general_pp: GeneralReport | null
  }
}

export interface ComparisonFilterRequest {
  parsers: string[]
  docs: string[]
  parser_reports?: InlineParserReports | null
}
