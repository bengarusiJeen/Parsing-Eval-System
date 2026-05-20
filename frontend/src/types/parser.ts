/* parser.ts — parser definitions for the UI */

export interface ParserInfo {
  id: string
  label: string
  icon: string
  desc: string
  available: boolean
}

export const PARSERS: ParserInfo[] = [
  { id: 'document_intelligence', label: 'Document Intelligence', icon: '◈', desc: 'Azure DI — OCR + layout',    available: true  },
  { id: 'pdf_pymupdf',           label: 'PyMuPDF',               icon: 'μ', desc: 'Native PDF text extraction', available: true  },
  { id: 'base_text_parser',      label: 'Base Text',             icon: '¶', desc: 'Plain text extraction',      available: true  },
  { id: 'mineru',                label: 'MinerU',                icon: '⛏', desc: 'Deep learning parser',       available: false },
  { id: 'marker',                label: 'Marker',                icon: '◊', desc: 'PDF → Markdown',             available: false },
  { id: 'surya',                 label: 'Surya',                 icon: '◎', desc: 'Multi-language OCR',         available: false },
]

export const parserLabel = (id: string): string =>
  PARSERS.find(p => p.id === id)?.label ?? id

export const parserIcon = (id: string): string =>
  PARSERS.find(p => p.id === id)?.icon ?? '◇'
