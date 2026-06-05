import {
  Activity,
  BarChart3,
  Database,
  FileUp,
  FileSearch,
  KeyRound,
  Layers3,
  ScanLine,
  Settings,
  ShieldCheck,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import type { ConsoleView, HealthPayload } from "@/types"
import { cn } from "@/lib/utils"

const navItems: Array<{
  id: ConsoleView
  label: string
  icon: typeof BarChart3
}> = [
  { id: "overview", label: "개요", icon: BarChart3 },
  { id: "scanner", label: "실시간 스캐너", icon: ScanLine },
  { id: "logs", label: "로그", icon: FileSearch },
  { id: "trace", label: "처리 추적", icon: Layers3 },
  { id: "batch", label: "배치", icon: Database },
  { id: "datasets", label: "데이터셋 실행", icon: FileUp },
  { id: "settings", label: "설정", icon: Settings },
]

interface AppShellProps {
  activeView: ConsoleView
  health: HealthPayload | null
  logEncryptionKey: string
  logEncryptionHint: string
  onLogEncryptionKeyChange: (value: string) => void
  onLogEncryptionHintChange: (value: string) => void
  onViewChange: (view: ConsoleView) => void
  children: React.ReactNode
}

export function AppShell({
  activeView,
  health,
  logEncryptionKey,
  logEncryptionHint,
  onLogEncryptionKeyChange,
  onLogEncryptionHintChange,
  onViewChange,
  children,
}: AppShellProps) {
  const activeLabel = navItems.find((item) => item.id === activeView)?.label ?? "개요"
  const apiStatusLabel = health?.status === "ok" ? "정상" : (health?.status ?? "오프라인")
  const trimmedLogKey = logEncryptionKey.trim()
  const logEncryptionReady = trimmedLogKey.length >= 8
  const logEncryptionLabel = logEncryptionReady ? "자동 암호화" : trimmedLogKey ? "8자 이상" : "키 필요"

  return (
    <div className="min-h-screen bg-background text-foreground">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r bg-sidebar/95 px-3 py-4 lg:flex lg:flex-col">
        <div className="flex items-center gap-3 px-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">Korean PII Guardrail</div>
            <div className="truncate text-xs text-muted-foreground">로컬 콘솔</div>
          </div>
        </div>
        <Separator className="my-4" />
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <Button
                key={item.id}
                type="button"
                variant={activeView === item.id ? "secondary" : "ghost"}
                className={cn(
                  "h-9 w-full justify-start gap-2 px-2 text-sm",
                  activeView === item.id && "bg-accent text-accent-foreground",
                )}
                onClick={() => onViewChange(item.id)}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Button>
            )
          })}
        </nav>
        <div className="mt-auto space-y-3 rounded-md border bg-card p-3">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-muted-foreground">API</span>
            <Badge variant={health?.status === "ok" ? "default" : "destructive"}>
              {apiStatusLabel}
            </Badge>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Activity className="h-3.5 w-3.5" />
            <span className="truncate">{health?.ner_mode ?? "대기 중"}</span>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 border-b bg-background/95 px-4 py-3 backdrop-blur lg:px-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-xs text-muted-foreground">Korean PII Guardrail</div>
              <h1 className="text-lg font-semibold leading-tight">{activeLabel}</h1>
            </div>
            <div className="flex flex-wrap items-center justify-end gap-2">
              <div className="flex min-w-0 items-center gap-2 rounded-md border bg-card/70 px-2 py-1">
                <KeyRound className="h-4 w-4 shrink-0 text-primary" />
                <Input
                  type="password"
                  value={logEncryptionKey}
                  onChange={(event) => onLogEncryptionKeyChange(event.target.value)}
                  aria-label="로그 암호화 키"
                  placeholder="로그 암호화 키"
                  className="h-7 w-[150px] border-0 bg-transparent px-1 shadow-none focus-visible:ring-0"
                />
                <Input
                  value={logEncryptionHint}
                  onChange={(event) => onLogEncryptionHintChange(event.target.value)}
                  aria-label="로그 암호화 키 힌트"
                  placeholder="힌트"
                  className="hidden h-7 w-[96px] border-0 bg-transparent px-1 shadow-none focus-visible:ring-0 xl:block"
                />
              </div>
              <Badge variant={logEncryptionReady ? "default" : "outline"} className="hidden sm:inline-flex">
                원문 로그: {logEncryptionLabel}
              </Badge>
              <Badge variant={health?.status === "ok" ? "default" : "secondary"}>
                {health?.version ?? "연결 중"}
              </Badge>
            </div>
          </div>
          <nav className="mt-3 flex gap-2 overflow-x-auto lg:hidden">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Button
                  key={item.id}
                  type="button"
                  size="sm"
                  variant={activeView === item.id ? "secondary" : "outline"}
                  className="h-8 shrink-0 gap-1.5"
                  onClick={() => onViewChange(item.id)}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {item.label}
                </Button>
              )
            })}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-[1500px] px-4 py-4 lg:px-6">{children}</main>
      </div>
    </div>
  )
}
