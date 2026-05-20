/* stream.ts — types for /api/stream_data */

export type StreamHighlightClass =
  | ''
  | 'hl-error'
  | 'hl-noise'
  | 'hl-format'
  | 'hl-fixed'
  | 'hl-missing'

export interface StreamSegment {
  text: string
  cls: StreamHighlightClass | string
}

export interface StreamData {
  gt:  StreamSegment[]
  raw: StreamSegment[]
  pp:  StreamSegment[]
  has_gt:  boolean
  has_raw: boolean
  has_pp:  boolean
}
