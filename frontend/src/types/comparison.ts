/* comparison.ts — types for /api/comparison/* */

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

/** Response from GET /api/comparison/info — drives the filter UI. */
export interface ComparisonInfoResponse {
  parsers: string[]
  docs:    string[]
}

/** Request body for POST /api/comparison/filter.
 *  parser_reports is intentionally omitted: the backend reads per-parser
 *  data from its own storage (last_run.json).  No evaluation data should
 *  flow from the frontend back to the backend.
 */
export interface ComparisonFilterRequest {
  parsers: string[]
  docs:    string[]
}
