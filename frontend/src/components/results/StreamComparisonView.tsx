/* StreamComparisonView — 3-column annotated text view (GT / Raw / PP). */

import { useEffect, useState } from 'react'

import { fetchStreamData } from '../../api/streamApi'
import { useAppState } from '../../state/AppContext'
import { parserLabel } from '../../types/parser'
import type { StreamData, StreamSegment } from '../../types/stream'

export function StreamComparisonView() {
  const {
    activeDoc,
    diagnostic,
    activeParser,
    selectedParsers,
  } = useAppState()

  if (activeDoc === 'summary') {
    return <div className="stream-no-data">
      Select a specific document tab to view the Stream Comparison.
    </div>
  }

  const diagDoc = (diagnostic?.documents ?? [])[activeDoc]
  if (!diagDoc) {
    return <div className="stream-no-data">No document data available.</div>
  }

  const docName     = diagDoc.doc_name
  const parserId    = activeParser ?? [...selectedParsers][0] ?? ''
  const parserName  = parserLabel(parserId)

  return (
    <StreamPanel docName={docName} parserName={parserName} />
  )
}

function StreamPanel({ docName, parserName }: {
  docName:    string
  parserName: string
}) {
  const [data,  setData]  = useState<StreamData | null>(null)
  const [err,   setErr]   = useState<string | null>(null)
  const [load,  setLoad]  = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoad(true); setErr(null); setData(null)
    fetchStreamData(docName)
      .then(d => { if (!cancelled) setData(d) })
      .catch(e => { if (!cancelled) setErr(String(e)) })
      .finally(() => { if (!cancelled) setLoad(false) })
    return () => { cancelled = true }
  }, [docName])

  if (err) {
    return (
      <div className="stream-no-data">
        Failed to load stream data for <strong>{docName}</strong>.<br />
        <span style={{ fontFamily: 'var(--f-mono)', fontSize: '0.78em', color: 'var(--danger)' }}>
          {err}
        </span>
      </div>
    )
  }

  return (
    <div className="stream-section">
      <div style={{
        fontFamily: 'var(--f-display)',
        fontSize: '1rem',
        fontWeight: 600,
        color: 'var(--text-1)',
        marginBottom: 3,
      }}>
        Document Stream Comparison
      </div>
      <div style={{ fontSize: '0.74rem', color: 'var(--text-3)', marginBottom: 14 }} dir="auto">
        {docName}
      </div>

      <Legend />

      <div className="stream-columns">
        <StreamCol label="Ground Truth (Expected)" name="Reference Document"
                   segments={data?.gt}  available={data?.has_gt}  loading={load} />
        <StreamCol label="Raw Parser Output" name={parserName}
                   segments={data?.raw} available={data?.has_raw} loading={load} />
        <StreamCol label="Post-Processed Output" name={parserName + ' + PP'}
                   segments={data?.pp}  available={data?.has_pp}  loading={load} />
      </div>
    </div>
  )
}

function Legend() {
  return (
    <div className="stream-legend">
      <span className="stream-legend-title">Legend</span>
      <span className="stream-legend-item">
        <span className="stream-legend-swatch" style={{
          background: 'rgba(220,38,38,0.15)',
          outline: '1px solid rgba(220,38,38,0.30)',
          borderRadius: 2,
        }} />
        Problem / Error
      </span>
      <span className="stream-legend-item">
        <span className="stream-legend-swatch" style={{
          background: 'rgba(220,38,38,0.09)',
          borderRadius: 2,
        }} />
        Noise (removed)
      </span>
      <span className="stream-legend-item">
        <span className="stream-legend-swatch" style={{
          background: 'rgba(180,83,9,0.13)',
          outline: '1px solid rgba(180,83,9,0.30)',
          borderRadius: 2,
        }} />
        Formatting / Spacing
      </span>
      <span className="stream-legend-item">
        <span className="stream-legend-swatch" style={{
          background: 'rgba(22,163,74,0.14)',
          outline: '1px solid rgba(22,163,74,0.30)',
          borderRadius: 2,
        }} />
        Fixed / Recovered
      </span>
      <span className="stream-legend-item">
        <span className="stream-legend-swatch" style={{
          background: 'rgba(220,38,38,0.06)',
          borderBottom: '2px solid rgba(220,38,38,0.35)',
          borderRadius: 2,
        }} />
        Missing from parser
      </span>
    </div>
  )
}

function StreamCol({ label, name, segments, available, loading }: {
  label:     string
  name:      string
  segments?: StreamSegment[]
  available?: boolean
  loading:   boolean
}) {
  return (
    <div className="stream-col">
      <div className="stream-col-hdr">
        <div className="stream-col-label">{label}</div>
        <div className="stream-col-name">{name}</div>
      </div>
      {loading ? (
        <div className="stream-col-body" style={{ color: 'var(--text-3)', fontSize: '0.78rem' }}>
          Loading…
        </div>
      ) : available ? (
        <div className="stream-col-body" dir="auto">
          {(segments ?? []).map((seg, i) =>
            seg.cls
              ? <span key={i} className={`hl ${seg.cls}`} dir="auto">{seg.text}</span>
              : <span key={i}>{seg.text}</span>
          )}
        </div>
      ) : (
        <div className="stream-col-body stream-no-data" style={{ fontSize: '0.78rem' }}>
          Not available for this document.
        </div>
      )}
    </div>
  )
}
