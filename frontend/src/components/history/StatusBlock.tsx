/* StatusBlock — uniform loading / error / empty rendering used by both
   the History and Corpora pages. Kept under components/history/ because
   that's where it was first introduced; the Corpora components import it
   from the same path. */

interface Props {
  state: 'loading' | 'error' | 'empty' | null
  message?: string
}

export function StatusBlock({ state, message }: Props) {
  if (state === null) return null

  const cls =
    state === 'error'
      ? 'history-status history-status--error'
      : 'history-status'

  const text =
    message ??
    (state === 'loading' ? 'Loading…' : state === 'error' ? 'Something went wrong.' : '')

  return <div className={cls}>{text}</div>
}
