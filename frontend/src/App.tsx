import { useEffect } from 'react'

import { fetchAvailableFiles } from './api/filesApi'
import { fetchCachedResults }  from './api/resultsApi'
import { Header }              from './components/layout/Header'
import { Sidebar }             from './components/layout/Sidebar'
import { SetupPage }           from './pages/SetupPage'
import { ResultsPage }         from './pages/ResultsPage'
import { ComparisonPage }      from './pages/ComparisonPage'
import { HistoryPage }         from './pages/HistoryPage'
import { CorporaPage }         from './pages/CorporaPage'
import { AppProvider, useAppState } from './state/AppContext'

function AppShell() {
  const {
    activeNav,
    setAvailableFiles,
    applyResponse,
    switchNav,
  } = useAppState()

  /* Bootstrap: fetch file list + try to load cached last-run results */
  useEffect(() => {
    let cancelled = false
    void (async () => {
      const files = await fetchAvailableFiles()
      if (cancelled) return
      setAvailableFiles(files)

      const cached = await fetchCachedResults()
      if (cancelled) return
      if (cached) {
        // Restores single- or multi-parser data (the latter repopulates
        // parserResults so the Compare page works after a reload).
        applyResponse(cached)
        switchNav('results')
      }
    })()
    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div id="app">
      <Header />
      <div id="body-wrap">
        <Sidebar />
        <div id="main-area">
          <div style={{ display: activeNav === 'setup'      ? 'flex' : 'none', flex: 1, flexDirection: 'column', overflow: 'hidden' }}>
            <SetupPage />
          </div>
          <div style={{ display: activeNav === 'results'    ? 'flex' : 'none', flex: 1, flexDirection: 'column', overflow: 'hidden' }}>
            <ResultsPage />
          </div>
          <div style={{ display: activeNav === 'comparison' ? 'flex' : 'none', flex: 1, flexDirection: 'column', overflow: 'hidden' }}>
            <ComparisonPage />
          </div>
          <div style={{ display: activeNav === 'history'    ? 'flex' : 'none', flex: 1, flexDirection: 'column', overflow: 'hidden' }}>
            <HistoryPage />
          </div>
          <div style={{ display: activeNav === 'corpora'    ? 'flex' : 'none', flex: 1, flexDirection: 'column', overflow: 'hidden' }}>
            <CorporaPage />
          </div>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  )
}

export default App
