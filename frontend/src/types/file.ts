/* file.ts — types for /api/files responses */

export interface FileEntry {
  name: string
  ext: string
}

export interface FilesResponse {
  files: FileEntry[]
}
