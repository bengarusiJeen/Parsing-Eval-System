/* corporaApi.ts — CRUD wrappers for /api/corpora/*. */

import { apiGet, apiPatch, apiPost } from './client'
import type {
  Corpus,
  CorpusCreatePayload,
  CorpusFile,
  CorpusFileAssignPayload,
  CorpusFileUpdatePayload,
  CorpusUpdatePayload,
} from '../types/corpus'

export const listCorpora = (includeInactive = false) =>
  apiGet<Corpus[]>(`/api/corpora?include_inactive=${includeInactive}`)

export const createCorpus = (payload: CorpusCreatePayload) =>
  apiPost<Corpus>('/api/corpora', payload)

export const updateCorpus = (id: number, payload: CorpusUpdatePayload) =>
  apiPatch<Corpus>(`/api/corpora/${id}`, payload)

export const listCorpusFiles = (id: number, includeInactive = false) =>
  apiGet<CorpusFile[]>(
    `/api/corpora/${id}/files?include_inactive=${includeInactive}`,
  )

export const assignCorpusFile = (id: number, payload: CorpusFileAssignPayload) =>
  apiPost<CorpusFile>(`/api/corpora/${id}/files`, payload)

export const updateCorpusFile = (
  id: number,
  fileName: string,
  payload: CorpusFileUpdatePayload,
) =>
  apiPatch<CorpusFile>(
    `/api/corpora/${id}/files/${encodeURIComponent(fileName)}`,
    payload,
  )
