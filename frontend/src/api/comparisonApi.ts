/* comparisonApi.ts — /api/comparison/* */

import { apiGet, apiPost } from './client'
import type {
  ComparisonFilterRequest,
  ComparisonInfoResponse,
  ComparisonResult,
} from '../types/comparison'

/** GET /api/comparison/info
 *  Returns the parsers and documents available for the Compare filter UI.
 *  The backend derives this from its own stored last-run snapshot — the
 *  frontend does not need to supply any evaluation data.
 */
export function fetchComparisonInfo(): Promise<ComparisonInfoResponse> {
  return apiGet<ComparisonInfoResponse>('/api/comparison/info')
}

/** POST /api/comparison/filter
 *  Returns ranked scores for the selected parsers and documents.
 *  The backend reads per-parser reports from storage; no inline report
 *  data is sent from the frontend.
 */
export function fetchComparison(
  req: ComparisonFilterRequest,
): Promise<ComparisonResult> {
  return apiPost<ComparisonResult>('/api/comparison/filter', req)
}
