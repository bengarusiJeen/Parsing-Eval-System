/* streamApi.ts — GET /api/stream_data */

import { apiGet } from './client'
import type { StreamData } from '../types/stream'

export function fetchStreamData(
  docName: string,
  parserId?: string,
): Promise<StreamData> {
  const params = new URLSearchParams({ doc: docName })
  if (parserId) params.set('parser', parserId)
  return apiGet<StreamData>(`/api/stream_data?${params.toString()}`)
}
