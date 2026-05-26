/* RunsSection — owns the runs list fetch and the currently-selected run. */

import { useCallback, useEffect, useState } from 'react'

import { ApiError } from '../../api/client'
import { fetchRuns } from '../../api/historyApi'
import type { RunSummary } from '../../types/history'

import { RunDetailsPanel } from './RunDetailsPanel'
import { RunsTable } from './RunsTable'
import { StatusBlock } from './StatusBlock'

type StatusState = 'loading' | 'error' | 'empty' | null

function friendlyApiError(err: unknown): string {
  if (err instanceof ApiError) return err.message
  if (err instanceof Error) return err.message
  return 'Unknown error'
}

export function RunsSection() {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [status, setStatus] = useState<StatusState>('loading')
  const [errorMsg, setErrorMsg] = useState<string>('')
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const load = useCallback(() => {
    let cancelled = false
    setStatus('loading')
    setErrorMsg('')
    fetchRuns(7)
      .then(list => {
        if (cancelled) return
        setRuns(list)
        setStatus(list.length === 0 ? 'empty' : null)
      })
      .catch(err => {
        if (cancelled) return
        setRuns([])
        setErrorMsg(friendlyApiError(err))
        setStatus('error')
      })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    const cleanup = load()
    return cleanup
  }, [load])

  return (
    <>
      <section className="report-section">
        <div className="sec-hdr">
          <h3>Recent runs</h3>
        </div>
        {status === null && (
          <RunsTable
            runs={runs}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onRefresh={() => { setSelectedId(null); load() }}
          />
        )}
        <StatusBlock
          state={status}
          message={
            status === 'error'   ? errorMsg :
            status === 'empty'   ? 'No runs recorded yet.' :
            status === 'loading' ? 'Loading runs…' : undefined
          }
        />
      </section>

      {selectedId != null && (
        <RunDetailsPanel runId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </>
  )
}
