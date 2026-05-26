/* TimelineChart — handcrafted SVG line chart, multi-series.
   - X axis: time (real timestamps; ticks are the union of all series' run times)
   - Y axis: metric value clamped to [0, 1]
   - One <path> + circle markers per series, each in its parser color
   - Hover over a marker → small tooltip showing that series' point
   - When fileSetChanged is true, a colored triangle sits above the marker
   - Designed for ≤30 points per series; not optimised for thousands. */

import { useEffect, useMemo, useRef, useState } from 'react'

import { pct } from '../../lib/format'
import { PARSERS } from '../../types/parser'
import type { TimelineMetric } from '../../types/history'

export interface ChartPoint {
  x: Date
  y: number | null
  runId: number
  fileSetChanged: boolean
  warning?: string | null
}

export interface ChartSeries {
  parserId: string
  parserLabel: string
  color: string
  points: ChartPoint[]
}

interface Props {
  series: ChartSeries[]
  metric: TimelineMetric
  height?: number
}

const PAD = { top: 16, right: 24, bottom: 36, left: 48 }
const Y_TICKS = [0, 0.25, 0.5, 0.75, 1.0]
const AXIS_LABEL_H = 28           // HTML axis-label row rendered above the SVG
const FALLBACK_COLOR = '#6b7280'

/* Stable palette keyed by parser index in the canonical PARSERS list.
   The first three available parsers (DI / PyMuPDF / Base) get the strongest
   contrast against each other. */
const PARSER_PALETTE = [
  '#4f46e5',  // indigo (var(--accent-2)) — Document Intelligence
  '#0d9488',  // teal                       — PyMuPDF
  '#d97706',  // amber                      — Base Text
  '#9333ea',  // violet                     — MinerU
  '#dc2626',  // red                        — Marker
  '#0369a1',  // sky    (var(--info))       — Surya
]

export function colorForParser(parserId: string): string {
  const idx = PARSERS.findIndex(p => p.id === parserId)
  if (idx < 0) return FALLBACK_COLOR
  return PARSER_PALETTE[idx % PARSER_PALETTE.length]
}

function formatTick(d: Date): string {
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}/${dd} ${hh}:${mi}`
}

function metricLabel(metric: TimelineMetric): string {
  return metric === 'avg_score' ? 'Avg score'
       : metric === 'coverage'  ? 'Coverage'
       :                          'Noise'
}

function higherIsBetter(metric: TimelineMetric): boolean {
  return metric !== 'noise'
}

interface HoverKey {
  seriesIdx: number
  pointIdx: number
}

export function TimelineChart({ series, metric, height = 240 }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(640)
  const [hover, setHover] = useState<HoverKey | null>(null)

  // Responsive width via ResizeObserver
  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(entries => {
      for (const e of entries) setWidth(Math.max(320, e.contentRect.width))
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const svgHeight = Math.max(80, height - AXIS_LABEL_H)
  const innerW = Math.max(1, width     - PAD.left - PAD.right)
  const innerH = Math.max(1, svgHeight - PAD.top  - PAD.bottom)

  // ── time domain ─────────────────────────────────────────────────────────
  // Collect every timestamp across all series; that union drives the x-axis
  // ticks and the x scale.
  const allTimes = useMemo(() => {
    const set = new Set<number>()
    for (const s of series) for (const p of s.points) set.add(p.x.getTime())
    return [...set].sort((a, b) => a - b)
  }, [series])

  const tMin = allTimes.length > 0 ? allTimes[0] : 0
  const tMax = allTimes.length > 0 ? allTimes[allTimes.length - 1] : 0

  const xPos = (t: number) => {
    if (allTimes.length <= 1 || tMax === tMin) return PAD.left + innerW / 2
    return PAD.left + ((t - tMin) / (tMax - tMin)) * innerW
  }
  const yPos = (v: number) => PAD.top + (1 - v) * innerH

  // Skip-every-other on the x-axis when there are more than 7 unique times.
  const skipLabel = (i: number) => allTimes.length > 7 && i % 2 !== 0

  // ── per-series paths ────────────────────────────────────────────────────
  const seriesPaths = useMemo(() => series.map(s => {
    let d = ''
    let started = false
    for (const p of s.points) {
      if (p.y == null) { started = false; continue }
      const cmd = started ? 'L' : 'M'
      d += `${cmd}${xPos(p.x.getTime()).toFixed(2)},${yPos(p.y).toFixed(2)} `
      started = true
    }
    return d.trim()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [series, width, height, tMin, tMax])

  const hovered =
    hover != null ? series[hover.seriesIdx]?.points[hover.pointIdx] ?? null : null
  const hoveredSeries = hover != null ? series[hover.seriesIdx] ?? null : null
  const hoveredX = hovered != null ? xPos(hovered.x.getTime()) : 0
  const hoveredY = hovered?.y != null ? yPos(hovered.y) : 0

  const totalPoints = series.reduce((n, s) => n + s.points.length, 0)
  if (totalPoints === 0) return null

  return (
    <div ref={wrapRef} className="history-chart-wrap" style={{ height }}>
      <div className="history-chart-axis-label">
        <span className="history-chart-axis-metric">{metricLabel(metric)}</span>
        <span className="history-chart-axis-hint">
          {higherIsBetter(metric) ? '↑ higher is better' : '↓ lower is better'}
        </span>
        {series.length > 0 && (
          <div className="history-chart-legend">
            {series.map(s => (
              <span key={s.parserId} className="history-chart-legend-item">
                <span
                  className="history-chart-legend-swatch"
                  style={{ background: s.color }}
                  aria-hidden="true"
                />
                {s.parserLabel}
              </span>
            ))}
          </div>
        )}
      </div>

      <svg width={width} height={svgHeight} role="img" aria-label="Timeline chart">
        {/* gridlines + y ticks */}
        {Y_TICKS.map(t => (
          <g key={t}>
            <line
              x1={PAD.left}
              x2={PAD.left + innerW}
              y1={yPos(t)}
              y2={yPos(t)}
              stroke="var(--border)"
              strokeDasharray="3 3"
            />
            <text
              x={PAD.left - 8}
              y={yPos(t) + 4}
              textAnchor="end"
              fontSize={11}
              fill="var(--text-3)"
            >
              {pct(t, 0)}
            </text>
          </g>
        ))}

        {/* x-axis baseline */}
        <line
          x1={PAD.left}
          x2={PAD.left + innerW}
          y1={PAD.top + innerH}
          y2={PAD.top + innerH}
          stroke="var(--border-2)"
        />

        {/* x ticks + labels — one per unique timestamp */}
        {allTimes.map((t, i) => (
          <g key={`xt-${t}`}>
            <line
              x1={xPos(t)}
              x2={xPos(t)}
              y1={PAD.top + innerH}
              y2={PAD.top + innerH + 4}
              stroke="var(--border-2)"
            />
            {!skipLabel(i) && (
              <text
                x={xPos(t)}
                y={PAD.top + innerH + 18}
                textAnchor="middle"
                fontSize={10}
                fill="var(--text-3)"
              >
                {formatTick(new Date(t))}
              </text>
            )}
          </g>
        ))}

        {/* one path per series */}
        {series.map((s, si) => seriesPaths[si] && (
          <path
            key={`p-${s.parserId}`}
            d={seriesPaths[si]}
            fill="none"
            stroke={s.color}
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}

        {/* markers + fsc badges + hit areas (per series, per point) */}
        {series.map((s, si) => s.points.map((p, pi) => {
          const cx = xPos(p.x.getTime())
          const isHovered = hover != null && hover.seriesIdx === si && hover.pointIdx === pi
          if (p.y == null) {
            return (
              <g key={`m-${si}-${pi}`}>
                <rect
                  x={cx - 4}
                  y={PAD.top + innerH - 4}
                  width={8}
                  height={8}
                  fill="none"
                  stroke={s.color}
                  strokeDasharray="2 2"
                  opacity={0.5}
                />
                <circle
                  cx={cx}
                  cy={PAD.top + innerH - 8}
                  r={8}
                  fill="transparent"
                  onMouseEnter={() => setHover({ seriesIdx: si, pointIdx: pi })}
                  onMouseLeave={() => setHover(null)}
                />
              </g>
            )
          }
          const cy = yPos(p.y)
          return (
            <g key={`m-${si}-${pi}`}>
              {p.fileSetChanged && (
                <polygon
                  points={`${cx},${cy - 14} ${cx - 5},${cy - 6} ${cx + 5},${cy - 6}`}
                  fill={s.color}
                  aria-label={`${s.parserLabel}: file set changed`}
                />
              )}
              <circle
                cx={cx}
                cy={cy}
                r={isHovered ? 6 : 4}
                fill={s.color}
                stroke="var(--surface)"
                strokeWidth={1.5}
              />
              {/* small invisible hit-target on top for easier hover */}
              <circle
                cx={cx}
                cy={cy}
                r={10}
                fill="transparent"
                onMouseEnter={() => setHover({ seriesIdx: si, pointIdx: pi })}
                onMouseLeave={() => setHover(null)}
              />
            </g>
          )
        }))}
      </svg>

      {hovered && hovered.y != null && hoveredSeries && (
        <div
          className="history-tooltip"
          style={{
            left: Math.min(Math.max(hoveredX + 12, 8), width - 260),
            top: Math.max(hoveredY + AXIS_LABEL_H - 12, AXIS_LABEL_H + 4),
          }}
        >
          <div className="history-tooltip-head">
            <span
              className="history-tooltip-swatch"
              style={{ background: hoveredSeries.color }}
              aria-hidden="true"
            />
            <strong>{hoveredSeries.parserLabel}</strong>
          </div>
          <div>Run #{hovered.runId} · {hovered.x.toLocaleString()}</div>
          <div>{metricLabel(metric)}: {pct(hovered.y)}</div>
          <div>File set changed: {hovered.fileSetChanged ? 'yes' : 'no'}</div>
          {hovered.warning && <div className="history-tooltip-warn">⚠ {hovered.warning}</div>}
        </div>
      )}
    </div>
  )
}
