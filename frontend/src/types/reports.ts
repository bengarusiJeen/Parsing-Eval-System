/* reports.ts — shared report types used across evaluation/results */

export interface CoverageBlock {
  unique_ngrams_checked_count: number
  missing_unique_ngrams_count: number
  coverage_rate: number
  total_missing_unique_ngrams_ratio: string
}

export interface BlockResult {
  block_index: number
  coverage: CoverageBlock
  /* Backend writes the missing-ngrams key with a dynamic n in the name
     (e.g. missing_trigrams_in_block). */
  [k: string]: unknown
}

export interface DocCoverage {
  coverage_rate: number
  unique_ngrams_checked_count: number
  missing_unique_ngrams_count: number
  total_missing_unique_ngrams_ratio: string
}

export interface DocNoise {
  unique_parser_words_checked: number
  noise_words_count: number
  noise_words: string[]
  noise_rate: number
  noise_ratio: string
}

export interface DocumentReport {
  doc_name: string
  coverage: DocCoverage
  noise: DocNoise
  gt_total_words_non_unique: number
  parser_total_words_non_unique: number
  block_results: BlockResult[]
}

export interface GeneralReportSummary {
  documents_evaluated: number
  avg_coverage_rate: number
  avg_noise_rate: number
}

export interface GeneralReport {
  summary: GeneralReportSummary
  documents: DocumentReport[]
}

/* ── Diagnostic report ───────────────────────────────────────── */

export interface OcrSplitIssue {
  original_word?: string
  word?: string
  fragments_in_parser?: string[]
  fragments?: string[]
}

export interface MergedWordIssue {
  original: string[]
  merged_word: string
}

export interface FormattingIssue {
  type?: string
  gt_text?: string
  parser_text?: string
  ngram?: string
  evidence?: string
  confidence?: 'HIGH' | 'MEDIUM' | string
}

export interface DetectedProblems {
  MISSING_BLOCK_PARSE: { count: number; blocks_number: number[] }
  OCR_SPLIT:           { count: number; issues: OcrSplitIssue[] }
  MERGED_WORDS:        { count: number; issues: MergedWordIssue[] }
  FORMATTING_ISSUES:   {
    count: number
    WORD_ORDER_REVERSAL?:   { issues: FormattingIssue[] }
    MISPLACED_PUNCTUATION?: { issues: FormattingIssue[] }
  }
  UNCLASSIFIED:        { count: number; ngrams: string[] }
}

export interface DiagnosticDocument {
  doc_name: string
  file_ext: string
  total_missing_ngrams: number
  detected_problems: DetectedProblems
}

export interface DiagnosticReport {
  documents: DiagnosticDocument[]
  [k: string]: unknown
}
