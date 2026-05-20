/* ComparisonFilters — pill checkboxes for parsers and documents */

import { parserLabel } from '../../types/parser'

interface FilterPillProps {
  label:    string
  checked:  boolean
  onToggle: () => void
}

function FilterPill({ label, checked, onToggle }: FilterPillProps) {
  return (
    <label className={`cmp-check-pill${checked ? ' checked' : ''}`} onClick={e => {
      e.preventDefault()
      onToggle()
    }}>
      <input type="checkbox" readOnly checked={checked} />
      <span>{label}</span>
    </label>
  )
}

interface Props {
  availableParsers: string[]
  availableDocs:    string[]
  selectedParsers:  Set<string>
  selectedDocs:     Set<string>
  toggleParser:     (id: string) => void
  toggleDoc:        (id: string) => void
}

export function ComparisonFilters({
  availableParsers,
  availableDocs,
  selectedParsers,
  selectedDocs,
  toggleParser,
  toggleDoc,
}: Props) {
  return (
    <div className="cmp-filter-bar">
      <div className="cmp-filter-group">
        <div className="cmp-filter-label">Parsers</div>
        <div className="cmp-filter-checks">
          {availableParsers.map(pid => (
            <FilterPill key={pid}
                        label={parserLabel(pid)}
                        checked={selectedParsers.has(pid)}
                        onToggle={() => toggleParser(pid)} />
          ))}
        </div>
      </div>
      <div className="cmp-filter-group">
        <div className="cmp-filter-label">Documents</div>
        <div className="cmp-filter-checks">
          {availableDocs.map(doc => (
            <FilterPill key={doc}
                        label={doc}
                        checked={selectedDocs.has(doc)}
                        onToggle={() => toggleDoc(doc)} />
          ))}
        </div>
      </div>
    </div>
  )
}
