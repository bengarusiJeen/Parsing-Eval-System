/* CorporaPage — corpus CRUD and file-assignment management. */

import { CorporaLayout } from '../components/corpora/CorporaLayout'

export function CorporaPage() {
  return (
    <div className="corpora-page">
      <header className="corpora-header">
        <h1>Corpora</h1>
        <p className="history-subtitle">
          Define document groups and weights that drive the overall timeline.
          Assignment only accepts files that already have a valid GT in the
          evaluation files directory.
        </p>
      </header>

      <div className="corpora-body">
        <CorporaLayout />
      </div>
    </div>
  )
}
