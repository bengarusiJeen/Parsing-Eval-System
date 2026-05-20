/* filesApi.ts — wrappers for GET /api/files */

import { apiGet } from './client'
import type { FilesResponse, FileEntry } from '../types/file'

export async function fetchAvailableFiles(): Promise<FileEntry[]> {
  try {
    const res = await apiGet<FilesResponse>('/api/files')
    return res.files ?? []
  } catch {
    return []
  }
}
