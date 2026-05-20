/* FileSelector — toolbar + list of available document folders */

import { useAppState } from '../../state/AppContext'

export function FileSelector() {
  const {
    availableFiles,
    selectedFiles,
    toggleFile,
    selectAllFiles,
    clearFiles,
  } = useAppState()

  const total = availableFiles.length
  const n     = selectedFiles.size
  const label = n === 0 ? '0 selected' : `${n} of ${total} selected`

  return (
    <>
      <div className="files-section-title">Files</div>
      <div className="setup-toolbar">
        <button type="button" className="setup-toolbar-btn" onClick={selectAllFiles}>Select All</button>
        <button type="button" className="setup-toolbar-btn" onClick={clearFiles}>Clear</button>
        <span id="file-count-badge" className={n > 0 ? 'has-selection' : ''}>
          {label}
        </span>
      </div>

      <div id="file-list">
        {availableFiles.length === 0 ? (
          <div style={{
            padding: 20,
            textAlign: 'center',
            color: 'var(--text-3)',
            fontSize: '0.82rem',
          }}>
            No document folders found in data/files_corpus/
          </div>
        ) : (
          availableFiles.map(f => {
            const sel = selectedFiles.has(f.name)
            const ext = f.ext || '—'
            return (
              <div
                key={f.name}
                className={`file-item${sel ? ' selected' : ''}`}
                onClick={() => toggleFile(f.name)}
              >
                <div className="file-checkbox">
                  <span className="file-checkbox-mark">
                    <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                      <path d="M1 4L3.5 6.5L9 1" stroke="#000" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </span>
                </div>
                <span className="file-ext-badge">{ext}</span>
                <span className="file-name" dir="auto" title={f.name}>{f.name}</span>
              </div>
            )
          })
        )}
      </div>
    </>
  )
}
