/* RunEvaluationButton — the "Start Evaluation" call-to-action */

import { useState } from 'react'

import { runEvaluation } from '../../api/evaluationApi'
import { useAppState } from '../../state/AppContext'

export function RunEvaluationButton() {
  const {
    selectedFiles,
    selectedParsers,
    includePostprocessing,
    setIncludePostprocessing,
    startEvaluation,
    applyResponse,
    showError,
  } = useAppState()
  const [running, setRunning] = useState(false)

  const canRun = selectedFiles.size > 0 && selectedParsers.size > 0
  const disabled = !canRun || running

  const onClick = async () => {
    if (!canRun) return
    setRunning(true)
    startEvaluation()
    try {
      const data = await runEvaluation({
        selected: [...selectedFiles],
        parsers:  [...selectedParsers],
        include_postprocessing: includePostprocessing,
      })
      applyResponse(data)
    } catch {
      showError('Could not reach the server.\nMake sure the FastAPI backend is running.')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="setup-footer">
      <label className="pp-toggle" title="Adds a second evaluation pass that applies postprocessing to parser output. Off by default — runs faster without it.">
        <input
          type="checkbox"
          checked={includePostprocessing}
          disabled={running}
          onChange={e => setIncludePostprocessing(e.target.checked)}
        />
        <span>Run postprocessing evaluation</span>
      </label>
      <button id="run-btn" type="button" disabled={disabled} onClick={onClick}>
        {running ? (
          <>
            <span className="btn-spinner" />
            Running…
          </>
        ) : (
          <>
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
              <path d="M2.5 1.5L10.5 6.5L2.5 11.5V1.5Z" fill="currentColor" />
            </svg>
            Start Evaluation
          </>
        )}
      </button>
      {!canRun && (
        <span className="setup-run-hint">Select at least one file to run</span>
      )}
    </div>
  )
}
