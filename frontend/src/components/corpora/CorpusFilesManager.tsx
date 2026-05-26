/* CorpusFilesManager — files for the selected corpus + assign-existing-file picker.
   File picker is a plain <select> of available files minus already-assigned ones
   (active OR inactive), per the MVP scope (no search/filter). */

import { useCallback, useEffect, useMemo, useState } from 'react'

import { ApiError } from '../../api/client'
import {
  assignCorpusFile,
  listCorpusFiles,
  updateCorpusFile,
} from '../../api/corporaApi'
import { useAppState } from '../../state/AppContext'
import type { CorpusFile } from '../../types/corpus'

import { StatusBlock } from '../history/StatusBlock'

interface Props {
  corpusId: number
  corpusName: string
  onBack: () => void
  onFilesChanged?: () => void   // bubbles up so timeline-by-corpus can re-fetch
}

function friendlyApiError(err: unknown): string {
  if (err instanceof ApiError) {
    const body = err.body as { detail?: unknown } | null
    const detail = body?.detail
    if (typeof detail === 'string') {
      // Map known short codes to friendly text where helpful
      return detail
    }
    if (detail && typeof detail === 'object') {
      const obj = detail as { code?: string; message?: string }
      if (obj.code && obj.message) {
        switch (obj.code) {
          case 'file_not_found':   return 'That file no longer exists in the evaluation files directory.'
          case 'corpus_not_found': return 'Corpus no longer exists. Reload the page.'
          case 'no_gt_folder':     return 'This file has no GT/ folder. Cannot assign without ground truth.'
          case 'invalid_gt':       return `GT for this file isn't parseable: ${obj.message}`
          case 'empty_gt':         return 'GT for this file produced no blocks; it would not score in evaluation.'
          default:                 return obj.message
        }
      }
      if ('message' in obj) return String(obj.message)
    }
    return err.message
  }
  if (err instanceof Error) return err.message
  return 'Unknown error'
}

export function CorpusFilesManager({
  corpusId,
  corpusName,
  onBack,
  onFilesChanged,
}: Props) {
  const { availableFiles } = useAppState()

  const [files, setFiles] = useState<CorpusFile[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [includeInactive, setIncludeInactive] = useState(false)

  const [showPicker, setShowPicker] = useState(false)
  const [pickerValue, setPickerValue] = useState<string>('')
  const [assignError, setAssignError] = useState<string | null>(null)
  const [assigning, setAssigning] = useState(false)
  const [toggleError, setToggleError] = useState<string | null>(null)

  // Always fetch with include_inactive=true so we know what's already assigned
  // (active or not) and can correctly exclude from the picker. Local toggle
  // simply controls the displayed list.
  const load = useCallback(() => {
    setLoading(true)
    setLoadError(null)
    listCorpusFiles(corpusId, true)
      .then(list => setFiles(list))
      .catch(err => setLoadError(friendlyApiError(err)))
      .finally(() => setLoading(false))
  }, [corpusId])

  useEffect(() => { load() }, [load])

  // Files visible in the list, filtered by includeInactive checkbox.
  const visibleFiles = useMemo(
    () => includeInactive ? files : files.filter(f => f.is_active),
    [files, includeInactive],
  )

  // Names already assigned (active OR inactive) — excluded from the picker.
  const assignedNames = useMemo(
    () => new Set(files.map(f => f.file_name)),
    [files],
  )

  const pickableFiles = useMemo(
    () => availableFiles.filter(f => !assignedNames.has(f.name)),
    [availableFiles, assignedNames],
  )

  const handleAssign = (e: React.FormEvent) => {
    e.preventDefault()
    if (!pickerValue) {
      setAssignError('Pick a file first.')
      return
    }
    setAssigning(true)
    setAssignError(null)
    assignCorpusFile(corpusId, { file_name: pickerValue })
      .then(() => {
        setPickerValue('')
        setShowPicker(false)
        load()
        onFilesChanged?.()
      })
      .catch(err => setAssignError(friendlyApiError(err)))
      .finally(() => setAssigning(false))
  }

  const setActive = (fileName: string, isActive: boolean) => {
    setToggleError(null)
    updateCorpusFile(corpusId, fileName, { is_active: isActive })
      .then(() => { load(); onFilesChanged?.() })
      .catch(err => setToggleError(friendlyApiError(err)))
  }

  return (
    <div className="corpora-side">
      <div className="sec-hdr corpora-side-hdr">
        <button type="button" className="cmp-view-btn" onClick={onBack}>← Back to list</button>
        <h3>{corpusName} · files</h3>
      </div>

      <div className="corpora-side-controls">
        <label className="corpora-form-row corpora-form-row--inline">
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={e => setIncludeInactive(e.target.checked)}
          />
          <span>Show inactive</span>
        </label>
        {!showPicker && (
          <button
            type="button"
            className="cmp-view-btn"
            onClick={() => { setShowPicker(true); setAssignError(null) }}
          >
            + Assign existing file
          </button>
        )}
      </div>

      {showPicker && (
        <form className="corpora-picker" onSubmit={handleAssign}>
          <label className="metric-label" htmlFor="cf-pick">Pick a file</label>
          <select
            id="cf-pick"
            className="history-select"
            value={pickerValue}
            onChange={e => setPickerValue(e.target.value)}
            disabled={pickableFiles.length === 0}
          >
            <option value="">— select —</option>
            {pickableFiles.map(f => (
              <option key={f.name} value={f.name}>{f.name}</option>
            ))}
          </select>
          {pickableFiles.length === 0 && (
            <span className="history-hint">All available files are already assigned to this corpus.</span>
          )}
          {assignError && (
            <div className="history-status history-status--error">{assignError}</div>
          )}
          <div className="corpora-form-actions">
            <button type="submit" className="cmp-view-btn" disabled={assigning || pickableFiles.length === 0}>
              {assigning ? 'Assigning…' : 'Assign'}
            </button>
            <button
              type="button"
              className="cmp-view-btn"
              onClick={() => { setShowPicker(false); setPickerValue(''); setAssignError(null) }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {toggleError && (
        <div className="history-status history-status--error">{toggleError}</div>
      )}

      {loading && <StatusBlock state="loading" message="Loading files…" />}
      {loadError && <StatusBlock state="error" message={loadError} />}
      {!loading && !loadError && visibleFiles.length === 0 && (
        <StatusBlock
          state="empty"
          message={
            files.length === 0
              ? 'No files assigned to this corpus yet.'
              : 'No active files. Toggle "Show inactive" to see deactivated assignments.'
          }
        />
      )}

      {!loading && !loadError && visibleFiles.length > 0 && (
        <ul className="corpora-files-ul">
          {visibleFiles.map(f => (
            <li
              key={f.id}
              className={`corpora-file-row${f.is_active ? '' : ' corpora-file-row--inactive'}`}
            >
              <span className="corpora-file-name">{f.file_name}</span>
              <span className={`history-status-pill ${f.is_active ? 'history-status-pill--ok' : 'history-status-pill--info'}`}>
                {f.is_active ? 'active' : 'inactive'}
              </span>
              {f.is_active ? (
                <button type="button" className="cmp-view-btn" onClick={() => setActive(f.file_name, false)}>
                  Deactivate
                </button>
              ) : (
                <button type="button" className="cmp-view-btn" onClick={() => setActive(f.file_name, true)}>
                  Activate
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
