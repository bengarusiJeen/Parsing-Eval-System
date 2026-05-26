/* CorporaLayout — two-pane composition (stacked on narrow screens).
   Left: CorpusManager (list, create, edit). Right: CorpusFilesManager when a
   corpus is selected. */

import { useCallback, useEffect, useState } from 'react'

import { listCorpora } from '../../api/corporaApi'
import type { Corpus } from '../../types/corpus'

import { CorpusFilesManager } from './CorpusFilesManager'
import { CorpusManager } from './CorpusManager'

export function CorporaLayout() {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [selectedName, setSelectedName] = useState<string>('')

  // Keep the selected corpus's name in sync with the latest list, in case
  // an Edit elsewhere changes it. Cheap re-fetch only when something changes.
  const refreshSelectedName = useCallback(() => {
    if (selectedId == null) return
    listCorpora(true)
      .then((list: Corpus[]) => {
        const found = list.find(c => c.id === selectedId)
        if (found) setSelectedName(found.name)
        else { setSelectedId(null); setSelectedName('') }
      })
      .catch(() => { /* ignore — manager surfaces its own errors */ })
  }, [selectedId])

  useEffect(() => {
    if (selectedId == null) { setSelectedName(''); return }
    refreshSelectedName()
  }, [selectedId, refreshSelectedName])

  return (
    <div className="corpora-layout">
      <CorpusManager
        selectedCorpusId={selectedId}
        onSelectCorpus={setSelectedId}
        onCorporaChanged={refreshSelectedName}
      />
      {selectedId != null && (
        <CorpusFilesManager
          corpusId={selectedId}
          corpusName={selectedName || `Corpus #${selectedId}`}
          onBack={() => setSelectedId(null)}
        />
      )}
    </div>
  )
}
