/* ComparisonTable — ranked table for either raw or post-processed scores */

import {
  coverageColor,
  noiseCleanColor,
  pct,
  rankBadgeClass,
} from '../../lib/format'
import { parserLabel } from '../../types/parser'
import { useAppState } from '../../state/AppContext'
import type { ParserCorpusScore } from '../../types/comparison'

interface Props {
  title:    string
  subBadge: string
  scores:   ParserCorpusScore[] | null
  rankAttr: 'rank_raw' | 'rank_post'
  covAttr:  'weighted_coverage_raw' | 'weighted_coverage_post'
  noiseAttr:'weighted_noise_raw'    | 'weighted_noise_post'
  errorText?: string | null
}

export function ComparisonTable({
  title, subBadge, scores, rankAttr, covAttr, noiseAttr, errorText,
}: Props) {
  const { switchParserTab, switchNav, selectDoc, setReport } = useAppState()

  const goToParser = (pid: string) => {
    switchParserTab(pid)
    selectDoc('summary')
    setReport('general')
    switchNav('results')
  }

  let body: React.ReactNode
  if (errorText) {
    body = <tr><td colSpan={5} className="cmp-empty">{errorText}</td></tr>
  } else if (!scores || scores.length === 0) {
    body = <tr><td colSpan={5} className="cmp-empty">No data available.</td></tr>
  } else {
    body = scores.map(s => {
      const rank  = s[rankAttr]
      const cov   = s[covAttr]
      const noise = s[noiseAttr]
      return (
        <tr key={s.parser_name}>
          <td><span className={`cmp-rank-badge ${rankBadgeClass(rank)}`}>{rank}</span></td>
          <td><span className="cmp-parser-name">{parserLabel(s.parser_name)}</span></td>
          <td className="num" style={{ color: coverageColor(cov), fontWeight: 600 }}>{pct(cov)}</td>
          <td className="num" style={{ color: noiseCleanColor(noise), fontWeight: 600 }}>{pct(noise)}</td>
          <td>
            <button type="button" className="cmp-view-btn"
                    onClick={() => goToParser(s.parser_name)}>
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M1.5 5h7M5.5 2L8.5 5l-3 3"
                      stroke="currentColor" strokeWidth="1.4"
                      strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              View Results
            </button>
          </td>
        </tr>
      )
    })
  }

  return (
    <div className="cmp-table-section">
      <div className="cmp-table-title">
        {title}
        <span className="cmp-pass-badge">{subBadge}</span>
      </div>
      <div className="cmp-table-wrap">
        <table className="cmp-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Parser</th>
              <th className="num">
                <span className="cmp-th-tip"
                      data-tip="How much of the document's expected content the parser actually found. Higher is better — 100% means nothing was missed.">
                  Coverage ⓘ
                </span>
              </th>
              <th className="num">
                <span className="cmp-th-tip"
                      data-tip="How much extra text the parser added that wasn't in the original document (headers, footers, artifacts, etc.). Lower is better — 0% means no extra noise.">
                  Noise ⓘ
                </span>
              </th>
              <th />
            </tr>
          </thead>
          <tbody>{body}</tbody>
        </table>
      </div>
    </div>
  )
}
