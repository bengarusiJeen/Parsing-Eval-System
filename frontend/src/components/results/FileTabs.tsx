/* FileTabs — Summary tab + per-doc tabs */

import { useAppState } from '../../state/AppContext'
import { docScore, scoreColor, trunc } from '../../lib/format'

export function FileTabs() {
  const { diagnostic, activeDoc, selectDoc } = useAppState()
  const docs = diagnostic?.documents ?? []

  return (
    <div id="tabs-bar">
      {/* Summary tab — always first */}
      <div
        className={`file-tab tab-summary${activeDoc === 'summary' ? ' active' : ''}`}
        onClick={() => selectDoc('summary')}
        title="Cross-document summary"
      >
        <span className="sum-icon">◈</span>
        <span>All Files</span>
      </div>

      {docs.map((doc, i) => {
        const score = docScore(doc)
        const color = scoreColor(score)
        const isAct = activeDoc === i
        return (
          <div
            key={`${doc.doc_name}-${i}`}
            className={`file-tab${isAct ? ' active' : ''}`}
            style={{ animationDelay: `${(i + 1) * 0.06}s` }}
            onClick={() => selectDoc(i)}
            title={doc.doc_name}
          >
            <span className="tab-sev-dot" style={{ background: color }} />
            <span style={{
              maxWidth: 130,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}>
              {trunc(doc.doc_name, 18)}
            </span>
            <span className="tab-ext">{doc.file_ext}</span>
          </div>
        )
      })}
    </div>
  )
}
