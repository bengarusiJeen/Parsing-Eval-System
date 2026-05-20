/* ParserSelector — grid of parser cards (multi-select) */

import { useAppState } from '../../state/AppContext'
import { PARSERS } from '../../types/parser'

export function ParserSelector() {
  const { selectedParsers, toggleParser } = useAppState()

  return (
    <div className="parser-section">
      <div className="parser-section-title">Parser</div>
      <div className="parser-grid">
        {PARSERS.map(p => {
          const selected = selectedParsers.has(p.id)
          const soon     = !p.available
          const className =
            'parser-card' +
            (selected ? ' selected' : '') +
            (soon ? ' parser-card--soon' : '')

          return (
            <div
              key={p.id}
              className={className}
              onClick={soon ? undefined : () => toggleParser(p.id)}
            >
              <div className="parser-card-top">
                <span className="parser-icon">{p.icon ?? '◇'}</span>
                {selected && <span className="parser-check-mark">✓</span>}
                <div className={`parser-badge ${soon ? 'parser-badge--soon' : 'parser-badge--live'}`}>
                  {soon ? 'Soon' : 'Live'}
                </div>
              </div>
              <div className="parser-name">{p.label}</div>
              <div className="parser-desc">{p.desc ?? ''}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
