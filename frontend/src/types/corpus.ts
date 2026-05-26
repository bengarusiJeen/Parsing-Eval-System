/* corpus.ts — types for /api/corpora/* responses. */

export interface Corpus {
  id: number
  name: string
  description: string | null
  overall_ratio: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CorpusFile {
  id: number
  corpus_id: number
  file_name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CorpusCreatePayload {
  name: string
  description?: string | null
  overall_ratio?: number
  is_active?: boolean
}

export interface CorpusUpdatePayload {
  name?: string
  description?: string | null
  overall_ratio?: number
  is_active?: boolean
}

export interface CorpusFileAssignPayload { file_name: string }
export interface CorpusFileUpdatePayload { is_active?: boolean }
