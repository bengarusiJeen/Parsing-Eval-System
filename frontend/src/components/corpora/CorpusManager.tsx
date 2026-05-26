/* CorpusManager — list + create + Edit/Save/Cancel inline form per corpus row.
   Explicit Edit/Save/Cancel actions (no save-on-blur) to avoid partial-save bugs. */

import { useCallback, useEffect, useState } from 'react'

import { ApiError } from '../../api/client'
import {
  createCorpus,
  listCorpora,
  updateCorpus,
} from '../../api/corporaApi'
import type { Corpus } from '../../types/corpus'

import { StatusBlock } from '../history/StatusBlock'

interface Props {
  selectedCorpusId: number | null
  onSelectCorpus: (id: number | null) => void
  onCorporaChanged?: () => void   // bubbles up so parent can refresh dependents
}

interface FormState {
  name: string
  description: string
  overall_ratio: string
  is_active: boolean
}

function friendlyApiError(err: unknown): string {
  if (err instanceof ApiError) {
    const body = err.body as { detail?: unknown } | null
    const detail = body?.detail
    if (typeof detail === 'string') return detail
    if (detail && typeof detail === 'object' && 'message' in detail) {
      return String((detail as { message?: unknown }).message ?? err.message)
    }
    return err.message
  }
  if (err instanceof Error) return err.message
  return 'Unknown error'
}

function corpusToForm(c: Corpus): FormState {
  return {
    name: c.name,
    description: c.description ?? '',
    overall_ratio: String(c.overall_ratio),
    is_active: c.is_active,
  }
}

const EMPTY_FORM: FormState = {
  name: '',
  description: '',
  overall_ratio: '0',
  is_active: true,
}

export function CorpusManager({
  selectedCorpusId,
  onSelectCorpus,
  onCorporaChanged,
}: Props) {
  const [corpora, setCorpora] = useState<Corpus[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  // Create-form state
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState<FormState>(EMPTY_FORM)
  const [createError, setCreateError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

  // Edit state
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<FormState>(EMPTY_FORM)
  const [editError, setEditError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(() => {
    setLoading(true)
    setLoadError(null)
    listCorpora(true)   // include_inactive=true so the manager shows everything
      .then(list => setCorpora(list))
      .catch(err => setLoadError(friendlyApiError(err)))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!createForm.name.trim()) {
      setCreateError('Name is required.')
      return
    }
    const ratio = Number(createForm.overall_ratio)
    if (!Number.isFinite(ratio) || ratio < 0) {
      setCreateError('Overall ratio must be a number ≥ 0.')
      return
    }
    setCreating(true)
    setCreateError(null)
    createCorpus({
      name: createForm.name.trim(),
      description: createForm.description.trim() || null,
      overall_ratio: ratio,
      is_active: createForm.is_active,
    })
      .then(() => {
        setCreateForm(EMPTY_FORM)
        setShowCreate(false)
        load()
        onCorporaChanged?.()
      })
      .catch(err => setCreateError(friendlyApiError(err)))
      .finally(() => setCreating(false))
  }

  const beginEdit = (c: Corpus) => {
    setEditingId(c.id)
    setEditForm(corpusToForm(c))
    setEditError(null)
  }
  const cancelEdit = () => {
    setEditingId(null)
    setEditError(null)
  }
  const saveEdit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingId == null) return
    if (!editForm.name.trim()) {
      setEditError('Name is required.')
      return
    }
    const ratio = Number(editForm.overall_ratio)
    if (!Number.isFinite(ratio) || ratio < 0) {
      setEditError('Overall ratio must be a number ≥ 0.')
      return
    }
    setSaving(true)
    setEditError(null)
    updateCorpus(editingId, {
      name: editForm.name.trim(),
      description: editForm.description.trim() || null,
      overall_ratio: ratio,
      is_active: editForm.is_active,
    })
      .then(() => {
        setEditingId(null)
        load()
        onCorporaChanged?.()
      })
      .catch(err => setEditError(friendlyApiError(err)))
      .finally(() => setSaving(false))
  }

  return (
    <div className="corpora-list">
      <div className="sec-hdr corpora-list-hdr">
        <h3>Corpora</h3>
        {!showCreate && (
          <button
            type="button"
            className="cmp-view-btn"
            onClick={() => { setShowCreate(true); setCreateError(null) }}
          >
            + New corpus
          </button>
        )}
      </div>

      {showCreate && (
        <form className="corpora-form corpora-corpus-card corpora-corpus-card--editing" onSubmit={handleCreate}>
          <div className="corpora-form-row">
            <label className="metric-label" htmlFor="cc-name">Name</label>
            <input
              id="cc-name"
              type="text"
              className="history-input"
              value={createForm.name}
              onChange={e => setCreateForm(f => ({ ...f, name: e.target.value }))}
              required
            />
          </div>
          <div className="corpora-form-row">
            <label className="metric-label" htmlFor="cc-desc">Description (optional)</label>
            <textarea
              id="cc-desc"
              className="history-input"
              rows={2}
              value={createForm.description}
              onChange={e => setCreateForm(f => ({ ...f, description: e.target.value }))}
            />
          </div>
          <div className="corpora-form-row">
            <label className="metric-label" htmlFor="cc-ratio">Overall ratio</label>
            <input
              id="cc-ratio"
              type="number"
              step="0.01"
              min={0}
              className="history-input history-input--narrow"
              value={createForm.overall_ratio}
              onChange={e => setCreateForm(f => ({ ...f, overall_ratio: e.target.value }))}
            />
          </div>
          <label className="corpora-form-row corpora-form-row--inline">
            <input
              type="checkbox"
              checked={createForm.is_active}
              onChange={e => setCreateForm(f => ({ ...f, is_active: e.target.checked }))}
            />
            <span>Active</span>
          </label>
          {createError && (
            <div className="history-status history-status--error">{createError}</div>
          )}
          <div className="corpora-form-actions">
            <button type="submit" className="cmp-view-btn" disabled={creating}>
              {creating ? 'Creating…' : 'Create'}
            </button>
            <button
              type="button"
              className="cmp-view-btn"
              onClick={() => { setShowCreate(false); setCreateForm(EMPTY_FORM); setCreateError(null) }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading && <StatusBlock state="loading" message="Loading corpora…" />}
      {loadError && <StatusBlock state="error" message={loadError} />}
      {!loading && !loadError && corpora.length === 0 && (
        <StatusBlock state="empty" message="No corpora yet. Create one above." />
      )}

      {!loading && !loadError && corpora.map(c => {
        const isSelected = c.id === selectedCorpusId
        const isEditing  = c.id === editingId

        if (isEditing) {
          return (
            <form
              key={c.id}
              className={`corpora-form corpora-corpus-card corpora-corpus-card--editing${
                isSelected ? ' corpora-corpus-card--selected' : ''
              }`}
              onSubmit={saveEdit}
            >
              <div className="corpora-form-row">
                <label className="metric-label">Name</label>
                <input
                  type="text"
                  className="history-input"
                  value={editForm.name}
                  onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))}
                  required
                />
              </div>
              <div className="corpora-form-row">
                <label className="metric-label">Description</label>
                <textarea
                  className="history-input"
                  rows={2}
                  value={editForm.description}
                  onChange={e => setEditForm(f => ({ ...f, description: e.target.value }))}
                />
              </div>
              <div className="corpora-form-row">
                <label className="metric-label">Overall ratio</label>
                <input
                  type="number"
                  step="0.01"
                  min={0}
                  className="history-input history-input--narrow"
                  value={editForm.overall_ratio}
                  onChange={e => setEditForm(f => ({ ...f, overall_ratio: e.target.value }))}
                />
              </div>
              <label className="corpora-form-row corpora-form-row--inline">
                <input
                  type="checkbox"
                  checked={editForm.is_active}
                  onChange={e => setEditForm(f => ({ ...f, is_active: e.target.checked }))}
                />
                <span>Active</span>
              </label>
              {editError && (
                <div className="history-status history-status--error">{editError}</div>
              )}
              <div className="corpora-form-actions">
                <button type="submit" className="cmp-view-btn" disabled={saving}>
                  {saving ? 'Saving…' : 'Save'}
                </button>
                <button type="button" className="cmp-view-btn" onClick={cancelEdit}>
                  Cancel
                </button>
              </div>
            </form>
          )
        }

        return (
          <div
            key={c.id}
            className={
              `corpora-corpus-card${c.is_active ? '' : ' corpora-corpus-card--inactive'}` +
              (isSelected ? ' corpora-corpus-card--selected' : '')
            }
          >
            <div className="corpora-corpus-card-head">
              <div>
                <div className="corpora-corpus-name">{c.name}</div>
                {c.description && (
                  <div className="corpora-corpus-desc">{c.description}</div>
                )}
              </div>
              <span className={`history-status-pill ${c.is_active ? 'history-status-pill--ok' : 'history-status-pill--info'}`}>
                {c.is_active ? 'active' : 'inactive'}
              </span>
            </div>
            <div className="corpora-corpus-meta">
              <span className="metric-label">overall_ratio</span>
              <span className="corpora-corpus-ratio">{c.overall_ratio}</span>
            </div>
            <div className="corpora-form-actions">
              <button type="button" className="cmp-view-btn" onClick={() => beginEdit(c)}>
                Edit
              </button>
              <button
                type="button"
                className="cmp-view-btn"
                onClick={() => onSelectCorpus(isSelected ? null : c.id)}
              >
                {isSelected ? 'Hide files' : 'Manage files →'}
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
