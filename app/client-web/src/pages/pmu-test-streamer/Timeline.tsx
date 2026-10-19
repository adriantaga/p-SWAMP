import { useEffect, useState } from 'react'

import type { PlayerStatus } from './usePmuStreamSocket'
import { formatInstant, formatSpan, formatUtc, parseUtc } from './time'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

/** The view spans offered, longest first; `null` is the whole coverage. Only
 *  those shorter than the coverage are offered. */
const SPANS: { label: string; seconds: number | null }[] = [
  { label: 'All', seconds: null },
  { label: '30 d', seconds: 30 * 86400 },
  { label: '1 d', seconds: 86400 },
  { label: '1 h', seconds: 3600 },
  { label: '1 min', seconds: 60 },
  { label: '10 s', seconds: 10 },
]

/** The nudges, each offered back and forward while shorter than the coverage. */
const NUDGES: { label: string; seconds: number }[] = [
  { label: '1 d', seconds: 86400 },
  { label: '1 h', seconds: 3600 },
  { label: '1 min', seconds: 60 },
  { label: '1 s', seconds: 1 },
]

const DAY_MS = 86_400_000

/**
 * Where the view window starts (epoch ms). It stays put while the cursor is in
 * it; when the cursor leaves it, it pages on to the cursor while playing, and
 * centres on it after a seek. Always inside the coverage.
 */
function placeWindow(at: number, cursor: number, span: number, start: number, end: number, playing: boolean): number {
  const latest = Math.max(start, end - span)
  if (at >= start && at <= latest && cursor >= at && cursor < at + span) return at
  return Math.min(Math.max(playing ? cursor : cursor - span / 2, start), latest)
}

/** Tick marks for the overview: calendar months over a long coverage, else
 *  the shortest round step giving at most eight. */
function ticks(start: number, end: number): { at: number; label: string }[] {
  const out: { at: number; label: string }[] = []
  if (end - start > 60 * DAY_MS) {
    const months = (end - start) / (30 * DAY_MS)
    const every = Math.ceil(months / 8)
    const first = new Date(start)
    for (let m = 1; ; m += every) {
      const at = Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + m, 1)
      if (at >= end) break
      out.push({ at, label: new Date(at).toISOString().slice(0, 7) })
    }
    return out
  }
  const steps = [1, 10, 60, 600, 3600, 6 * 3600, 86400, 7 * 86400].map((s) => s * 1000)
  const step = steps.find((s) => (end - start) / s <= 8) ?? 7 * DAY_MS
  for (let at = Math.ceil(start / step) * step; at < end; at += step) {
    const iso = new Date(at).toISOString()
    out.push({ at, label: step >= DAY_MS ? iso.slice(5, 10) : step >= 60_000 ? iso.slice(11, 16) : iso.slice(11, 19) })
  }
  return out
}

interface TimelineProps {
  player: PlayerStatus | undefined
  /** The timestamp of the frame at the cursor. */
  cursorAt: string | null
  /** Seconds between frames. */
  interval: number
  playing: boolean
  canSeek: boolean
  seek: (at: string) => void
}

/**
 * The recording's timeline, in UTC: what it covers, an overview of all of it
 * with the cursor and the view window, a slider over the view window (zoom it
 * with the view span), a jump to a typed instant, and nudges by a second up to
 * a day. Every control is a seek: the cursor moves when the server says so.
 */
export function Timeline({ player, cursorAt, interval, playing, canSeek, seek }: TimelineProps) {
  const coverageStart = canSeek ? player?.coverage_start : null
  const coverageEnd = canSeek ? player?.coverage_end : null
  const covered = Boolean(coverageStart && coverageEnd)
  const start = coverageStart ? Date.parse(coverageStart) : 0
  const end = coverageEnd ? Date.parse(coverageEnd) : 0
  const duration = (end - start) / 1000
  const cursor = cursorAt ? Date.parse(cursorAt) : start
  const last = Math.max(start, end - interval * 1000) // the latest instant a seek can name and land on a frame
  const clamped = (at: number) => new Date(Math.min(Math.max(at, start), last)).toISOString()
  const go = (at: number) => seek(clamped(at))

  const [spanLabel, setSpanLabel] = useState('All')
  const offered = SPANS.filter((s) => s.seconds === null || s.seconds < duration)
  const span = (offered.find((s) => s.label === spanLabel)?.seconds ?? duration) * 1000

  // Adjusted while rendering, not in an effect: the window follows the cursor.
  const [windowStart, setWindowStart] = useState(start)
  const placed = covered ? placeWindow(windowStart, cursor, span, start, end, playing) : windowStart
  if (placed !== windowStart) setWindowStart(placed)

  // The slider while dragged, in seconds from the window's start; null when it
  // follows the cursor. One seek on release, listened for on the window so a
  // release anywhere counts (and after a second, for the keyboard).
  const [scrub, setScrub] = useState<number | null>(null)
  const scrubTo = scrub === null ? null : clamped(placed + scrub * 1000)
  useEffect(() => {
    if (scrubTo === null) return
    const commit = () => {
      seek(scrubTo)
      setScrub(null)
    }
    const timer = setTimeout(commit, 1000)
    window.addEventListener('pointerup', commit)
    window.addEventListener('pointercancel', commit)
    return () => {
      clearTimeout(timer)
      window.removeEventListener('pointerup', commit)
      window.removeEventListener('pointercancel', commit)
    }
  }, [scrubTo, seek])

  // The jump field: typed text, or null while it shows the cursor.
  const [jump, setJump] = useState<string | null>(null)
  const jumpAt = jump === null ? Number.NaN : parseUtc(jump)
  const jumpable = covered && Number.isFinite(jumpAt) && jumpAt < end

  const fraction = (at: number) => (end > start ? (at - start) / (end - start) : 0)
  const ms = span <= 60_000
  return (
    <div className="flex w-full flex-col gap-2 text-xs text-muted-foreground">
      <div className="flex items-center gap-3">
        <span className="tabular-nums" data-testid="coverage-readout">
          {covered
            ? `Coverage ${formatInstant(start, { ms: duration < 60 })} → ${formatUtc(end, { ms: duration < 60 })} · ${formatSpan(duration)}`
            : 'Coverage —'}
        </span>
        <Select value={spanLabel} onValueChange={setSpanLabel} disabled={!covered || offered.length < 2}>
          <SelectTrigger size="sm" className="ml-auto w-24" aria-label="View span">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {offered.map((s) => (
              <SelectItem key={s.label} value={s.label}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* The whole coverage: a click seeks there. */}
      <button
        type="button"
        aria-label="Coverage overview"
        className="relative h-5 w-full overflow-hidden rounded-sm border bg-muted disabled:opacity-50"
        disabled={!covered}
        onClick={(event) => {
          const box = event.currentTarget.getBoundingClientRect()
          go(start + ((event.clientX - box.left) / box.width) * (end - start))
        }}
      >
        <span
          className="absolute inset-y-0 border-x border-primary bg-primary/20"
          style={{ left: `${fraction(placed) * 100}%`, width: `max(2px, ${(span / Math.max(end - start, 1)) * 100}%)` }}
        />
        {covered && cursorAt && (
          <span className="absolute inset-y-0 w-0.5 bg-red-600" style={{ left: `${fraction(cursor) * 100}%` }} />
        )}
      </button>
      <div className="relative h-4 overflow-hidden leading-4 tabular-nums">
        {covered &&
          ticks(start, end).map((tick) => (
            <span key={tick.at} className="absolute -translate-x-1/2 whitespace-nowrap" style={{ left: `${fraction(tick.at) * 100}%` }}>
              {tick.label}
            </span>
          ))}
      </div>

      {/* The view window: the slider's whole length. */}
      <div className="flex flex-col gap-0.5">
        <input
          type="range"
          aria-label="Seek"
          className="w-full"
          min={0}
          max={Math.max(span / 1000 - interval, 0)}
          step={interval}
          value={scrub ?? (covered ? Math.min(Math.max((cursor - placed) / 1000, 0), span / 1000) : 0)}
          disabled={!covered}
          onChange={(event) => setScrub(Number(event.target.value))}
        />
        <div className="flex justify-between gap-3 tabular-nums">
          <span>{covered ? formatInstant(placed, { ms }) : '—'}</span>
          <span>{covered ? formatInstant(Math.min(placed + span, end), { ms }) : '—'}</span>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-1">
        {NUDGES.filter((n) => n.seconds < duration).map((n) => (
          <Button key={`-${n.label}`} variant="outline" size="xs" aria-label={`Back ${n.label}`} disabled={!covered} onClick={() => go(cursor - n.seconds * 1000)}>
            −{n.label}
          </Button>
        ))}
        <form
          className="mx-2 flex items-center gap-1"
          onSubmit={(event) => {
            event.preventDefault()
            if (!jumpable) return
            go(jumpAt)
            setJump(null)
          }}
        >
          <input
            type="text"
            aria-label="Jump to (UTC)"
            placeholder="YYYY-MM-DD HH:MM:SS.mmm"
            spellCheck={false}
            className="w-48 rounded-md border bg-background px-2 py-1 text-foreground tabular-nums aria-invalid:border-destructive disabled:opacity-50"
            value={jump ?? (cursorAt ? formatInstant(cursorAt) : '')}
            aria-invalid={jump !== null && !jumpable}
            disabled={!covered}
            onChange={(event) => setJump(event.target.value)}
          />
          <span>UTC</span>
          <Button type="submit" variant="outline" size="xs" disabled={!jumpable}>
            Go
          </Button>
        </form>
        {[...NUDGES].reverse().filter((n) => n.seconds < duration).map((n) => (
          <Button key={`+${n.label}`} variant="outline" size="xs" aria-label={`Forward ${n.label}`} disabled={!covered} onClick={() => go(cursor + n.seconds * 1000)}>
            +{n.label}
          </Button>
        ))}
      </div>
    </div>
  )
}
