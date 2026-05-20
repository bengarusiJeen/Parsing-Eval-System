/* streamApi.ts — GET /api/stream_data */

import { apiGet } from './client'
import type { StreamData } from '../types/stream'

export function fetchStreamData(docName: string): Promise<StreamData> {
  return apiGet<StreamData>(`/api/stream_data?doc=${encodeURIComponent(docName)}`)
}
