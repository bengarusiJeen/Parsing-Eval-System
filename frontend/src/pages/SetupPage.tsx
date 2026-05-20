/* SetupPage — parser selection + file list + run button */

import { ParserSelector }       from '../components/setup/ParserSelector'
import { FileSelector }         from '../components/setup/FileSelector'
import { RunEvaluationButton }  from '../components/setup/RunEvaluationButton'

export function SetupPage() {
  return (
    <div id="setup-panel">
      <div className="setup-header">
        <div className="setup-title">Test Setup</div>
        <div className="setup-sub">Select files to include in the evaluation</div>
      </div>

      <ParserSelector />
      <FileSelector />
      <RunEvaluationButton />
    </div>
  )
}
