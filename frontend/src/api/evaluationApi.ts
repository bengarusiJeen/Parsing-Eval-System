/* evaluationApi.ts — POST /api/evaluate */

import { apiPost } from './client'
import type { EvaluateRequest, EvaluateResponse } from '../types/evaluation'

export function runEvaluation(req: EvaluateRequest): Promise<EvaluateResponse> {
  return apiPost<EvaluateResponse>('/api/evaluate', req)
}
