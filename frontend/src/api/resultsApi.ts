/* resultsApi.ts — GET /api/results (last-run reports from disk) */

import { apiGet } from './client'
import type {
  ResultsResponse,
  SingleParserResult,
} from '../types/evaluation'

/** Returns the cached results, or null if none exist. */
export async function fetchCachedResults(): Promise<SingleParserResult | null> {
  try {
    const data = await apiGet<ResultsResponse>('/api/results')
    if (data.status === 'no_results') return null
    return data
  } catch {
    return null
  }
}
