/* resultsApi.ts — GET /api/results (last-run reports from disk) */

import { apiGet } from './client'
import type {
  EvaluateResponse,
  ResultsResponse,
} from '../types/evaluation'

/** Returns the cached last-run result (single- or multi-parser), or null if none exist. */
export async function fetchCachedResults(): Promise<EvaluateResponse | null> {
  try {
    const data = await apiGet<ResultsResponse>('/api/results')
    if ('status' in data && data.status === 'no_results') return null
    return data as EvaluateResponse
  } catch {
    return null
  }
}
