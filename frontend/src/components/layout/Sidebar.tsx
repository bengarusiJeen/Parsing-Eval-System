/* Sidebar — left navigation: Setup / Results / Compare */

import { useAppState } from '../../state/AppContext'
import type { NavView } from '../../state/AppContext'

interface NavDef {
  id: NavView
  label: string
  icon: React.ReactNode
}

const NAVS: NavDef[] = [
  {
    id: 'setup',
    label: 'Setup',
    icon: (
      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M7.5 1C4 1 1 4 1 7.5S4 14 7.5 14 14 11 14 7.5 11 1 7.5 1Z" stroke="currentColor" strokeWidth="1.3" />
        <path d="M7.5 4.5V7.5L9.5 9.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    id: 'results',
    label: 'Results',
    icon: (
      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="1.5" y="1.5" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.3" />
        <path d="M4 5h7M4 7.5h5M4 10h3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    id: 'comparison',
    label: 'Compare',
    icon: (
      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="1" y="3" width="5.5" height="9" rx="1.2" stroke="currentColor" strokeWidth="1.3" />
        <rect x="8.5" y="3" width="5.5" height="9" rx="1.2" stroke="currentColor" strokeWidth="1.3" />
      </svg>
    ),
  },
  {
    id: 'history',
    label: 'History',
    icon: (
      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M1.5 11.5L5 8L8 10.5L13.5 4.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="5" cy="8" r="1.1" fill="currentColor" />
        <circle cx="8" cy="10.5" r="1.1" fill="currentColor" />
        <circle cx="13.5" cy="4.5" r="1.1" fill="currentColor" />
      </svg>
    ),
  },
  {
    id: 'corpora',
    label: 'Corpora',
    icon: (
      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M2 4.2v6.4c0 .4.2.7.6.9l4.5 1.6c.3.1.5.1.8 0l4.5-1.6c.4-.2.6-.5.6-.9V4.2" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
        <path d="M2 4.2l5.5-1.9 5.5 1.9-5.5 1.9z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
        <path d="M7.5 6.1v6.6" stroke="currentColor" strokeWidth="1.3" />
      </svg>
    ),
  },
]

export function Sidebar() {
  const { activeNav, switchNav } = useAppState()
  return (
    <nav id="sidebar">
      {NAVS.map(n => (
        <button
          key={n.id}
          type="button"
          className={`nav-item${activeNav === n.id ? ' active' : ''}`}
          onClick={() => switchNav(n.id)}
        >
          {n.icon}
          <span>{n.label}</span>
        </button>
      ))}
    </nav>
  )
}
