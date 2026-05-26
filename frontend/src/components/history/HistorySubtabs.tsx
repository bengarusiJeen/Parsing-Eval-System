/* HistorySubtabs — pill toggle inside HistoryPage: Timeline | Runs.
   Mirrors the .rpt-toggle pattern from results/ReportToggle.tsx. */

export type HistoryView = 'timeline' | 'runs'

interface Props {
  active: HistoryView
  onChange: (next: HistoryView) => void
}

interface Opt { id: HistoryView; label: string }
const OPTIONS: Opt[] = [
  { id: 'timeline', label: 'Timeline' },
  { id: 'runs',     label: 'Runs'     },
]

export function HistorySubtabs({ active, onChange }: Props) {
  return (
    <div className="rpt-toggle" role="tablist" aria-label="History sections">
      {OPTIONS.map(o => (
        <button
          key={o.id}
          type="button"
          role="tab"
          aria-selected={active === o.id}
          className={`rpt-opt${active === o.id ? ' active' : ''}`}
          onClick={() => onChange(o.id)}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}
