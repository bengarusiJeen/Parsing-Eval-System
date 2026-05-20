/* ParserSubtabs — only shown for multi-parser runs, lets the user switch parser */

import { useAppState } from '../../state/AppContext'
import { parserIcon, parserLabel } from '../../types/parser'

export function ParserSubtabs() {
  const { parserResults, activeParser, switchParserTab } = useAppState()

  const ids = Object.keys(parserResults)
  if (ids.length <= 1) return null

  return (
    <div id="parser-subtabs-bar">
      <span id="parser-subtabs-label">Parser</span>
      {ids.map(id => {
        const d      = parserResults[id]
        const isErr  = d.status !== 'ok'
        const isAct  = id === activeParser
        const cls    =
          'parser-subtab' +
          (isAct ? ' active' : '') +
          (isErr ? ' parser-subtab--error' : '')
        return (
          <div key={id} className={cls} onClick={() => switchParserTab(id)}>
            <span className="parser-subtab-icon">{parserIcon(id)}</span>
            <span>{parserLabel(id)}</span>
            {isErr && <span className="parser-subtab-err">⚠</span>}
          </div>
        )
      })}
    </div>
  )
}
