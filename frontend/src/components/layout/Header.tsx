/* Header — top bar with logo and status pill */

import { StatusPill } from './StatusPill'

export function Header() {
  return (
    <header id="header">
      <div className="logo">
        <div className="logo-mark">P</div>
        ParserDiag
        <span className="logo-badge">POC</span>
      </div>
      <div className="header-spacer" />
      <StatusPill />
    </header>
  )
}
