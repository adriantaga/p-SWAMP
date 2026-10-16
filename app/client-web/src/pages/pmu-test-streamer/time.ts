/** UTC instants for the streamer's page: everything it shows and sends is UTC. */

/** Seconds from one ISO instant to another. */
export function secondsBetween(from?: string | null, to?: string | null): number | null {
  return from && to ? (new Date(to).getTime() - new Date(from).getTime()) / 1000 : null
}

/** `iso` moved by `seconds`, as an ISO instant. Milliseconds only: send a
 *  frame's own timestamp, not one rebuilt from it, where microseconds matter. */
export function addSeconds(iso: string, seconds: number): string {
  return new Date(new Date(iso).getTime() + seconds * 1000).toISOString()
}

/** `2026-01-01 00:00:00.050`, without the zone; `ms: false` drops the milliseconds. */
export function formatInstant(iso: string | number, { ms = true }: { ms?: boolean } = {}): string {
  const text = new Date(iso).toISOString().replace('T', ' ')
  return ms ? text.slice(0, 23) : text.slice(0, 19)
}

/** `2026-01-01 00:00:00.050 UTC`; `ms: false` drops the milliseconds. */
export function formatUtc(iso: string | number, options: { ms?: boolean } = {}): string {
  return `${formatInstant(iso, options)} UTC`
}

/** A length of time: `2.50 s` under a minute, `2 d 19 h 55 min` above. */
export function formatSpan(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(2)} s`
  let rest = Math.round(seconds)
  const parts: string[] = []
  for (const [unit, size] of [['d', 86400], ['h', 3600], ['min', 60], ['s', 1]] as const) {
    const value = Math.floor(rest / size)
    rest -= value * size
    if (value) parts.push(`${value} ${unit}`)
  }
  return parts.join(' ')
}

/** A typed instant, read as UTC, as epoch milliseconds: `2026-01-11`, `2026-01-11 13:05`,
 *  `2026-01-11 13:05:00.040`, with or without a `T`, ` UTC` or `Z`, so a readout or a
 *  tray timestamp can be pasted. NaN when it is not one. */
export function parseUtc(text: string): number {
  const match = text.trim().match(/^(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?))?\s*(?:UTC|Z)?$/i)
  return match ? Date.parse(`${match[1]}T${match[2] ?? '00:00'}Z`) : Number.NaN
}
