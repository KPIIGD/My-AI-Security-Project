import { useCallback, useEffect, useState } from "react"

import { AppShell } from "@/components/app-shell"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { TooltipProvider } from "@/components/ui/tooltip"
import { getHealth, getLogs, getMetrics } from "@/lib/api"
import { BatchPage } from "@/pages/batch-page"
import { DatasetRunsPage } from "@/pages/dataset-runs-page"
import { LogsPage } from "@/pages/logs-page"
import { OverviewPage } from "@/pages/overview-page"
import { ScannerPage } from "@/pages/scanner-page"
import { SettingsPage } from "@/pages/settings-page"
import { TracePage } from "@/pages/trace-page"
import type { ApplyResponse, ConsoleView, HealthPayload, LogSummary, MetricsPayload } from "@/types"

export default function App() {
  const [activeView, setActiveView] = useState<ConsoleView>("overview")
  const [health, setHealth] = useState<HealthPayload | null>(null)
  const [metrics, setMetrics] = useState<MetricsPayload | null>(null)
  const [logs, setLogs] = useState<LogSummary[]>([])
  const [latestInput, setLatestInput] = useState("")
  const [latestResult, setLatestResult] = useState<ApplyResponse | null>(null)
  const [logEncryptionKey, setLogEncryptionKey] = useState("")
  const [logEncryptionHint, setLogEncryptionHint] = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refreshData = useCallback(async () => {
    setError(null)
    try {
      const [nextHealth, nextMetrics, nextLogs] = await Promise.all([
        getHealth(),
        getMetrics(),
        getLogs(100),
      ])
      setHealth(nextHealth)
      setMetrics(nextMetrics)
      setLogs(nextLogs)
    } catch (err) {
      setError(err instanceof Error ? err.message : "API 요청 실패")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshData()
  }, [refreshData])

  function handleScannerResult(input: string, result: ApplyResponse) {
    setLatestInput(input)
    setLatestResult(result)
  }

  return (
    <TooltipProvider>
      <AppShell
        activeView={activeView}
        health={health}
        logEncryptionKey={logEncryptionKey}
        logEncryptionHint={logEncryptionHint}
        onLogEncryptionKeyChange={setLogEncryptionKey}
        onLogEncryptionHintChange={setLogEncryptionHint}
        onViewChange={setActiveView}
      >
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertTitle>API 연결 실패</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {activeView === "overview" && (
          <OverviewPage health={health} metrics={metrics} logs={logs} loading={loading} />
        )}
        {activeView === "scanner" && (
          <ScannerPage
            result={latestResult}
            inputText={latestInput}
            logEncryptionKey={logEncryptionKey}
            logEncryptionHint={logEncryptionHint}
            onResult={handleScannerResult}
            onRefreshData={() => void refreshData()}
          />
        )}
        {activeView === "logs" && <LogsPage logs={logs} />}
        {activeView === "trace" && <TracePage />}
        {activeView === "batch" && (
          <BatchPage
            logEncryptionKey={logEncryptionKey}
            logEncryptionHint={logEncryptionHint}
            onRefreshData={() => void refreshData()}
          />
        )}
        {activeView === "datasets" && <DatasetRunsPage health={health} />}
        {activeView === "settings" && <SettingsPage health={health} metrics={metrics} />}
      </AppShell>
    </TooltipProvider>
  )
}
