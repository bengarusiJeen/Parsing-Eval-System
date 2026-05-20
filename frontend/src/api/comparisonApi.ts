/* comparisonApi.ts — POST /api/comparison/filter */

import { apiPost } from './client'
import type {
  ComparisonFilterRequest,
  ComparisonResult,
} from '../types/comparison'

export function fetchComparison(
  req: ComparisonFilterRequest,
): Promise<ComparisonResult> {
  return apiPost<ComparisonResult>('/api/comparison/filter', req)
}
