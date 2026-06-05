import { KeyRound, Loader2, Search, Unlock } from "lucide-react"
import { useMemo, useState } from "react"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { SpanTable } from "@/components/span-table"
import { StatusBadge } from "@/components/status-badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { decryptLog, getLogDetail } from "@/lib/api"
import { formatDateTime, formatMs, shortId } from "@/lib/format"
import type { LogDetail, LogSummary } from "@/types"

interface LogsPageProps {
  logs: LogSummary[]
}

export function LogsPage({ logs }: LogsPageProps) {
  const [query, setQuery] = useState("")
  const [detail, setDetail] = useState<LogDetail | null>(null)
  const [open, setOpen] = useState(false)
  const [decryptKey, setDecryptKey] = useState("")
  const [decryptedText, setDecryptedText] = useState<string | null>(null)
  const [decryptError, setDecryptError] = useState<string | null>(null)
  const [decrypting, setDecrypting] = useState(false)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) {
      return logs
    }
    return logs.filter((row) => {
      const haystack = [
        row.request_id,
        row.policy_profile,
        row.output_target,
        ...Object.keys(row.entity_counts),
        ...Object.keys(row.action_counts),
      ]
        .join(" ")
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [logs, query])

  async function openDetail(requestId: string) {
    const nextDetail = await getLogDetail(requestId)
    setDecryptKey("")
    setDecryptedText(null)
    setDecryptError(null)
    setDetail(nextDetail)
    setOpen(true)
  }

  function handleSheetOpenChange(nextOpen: boolean) {
    setOpen(nextOpen)
    if (!nextOpen) {
      setDecryptKey("")
      setDecryptedText(null)
      setDecryptError(null)
    }
  }

  async function handleDecrypt() {
    if (!detail || !decryptKey.trim()) {
      return
    }
    setDecrypting(true)
    setDecryptError(null)
    setDecryptedText(null)
    try {
      const response = await decryptLog(detail.request_id, decryptKey.trim())
      setDecryptedText(response.decrypted_text)
    } catch (err) {
      setDecryptError(readableError(err))
    } finally {
      setDecrypting(false)
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-sm">요청 로그</CardTitle>
          <div className="relative w-full sm:w-[340px]">
            <Search className="pointer-events-none absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="요청, 엔티티, 액션 검색"
              className="h-9 pl-8"
            />
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-hidden rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>요청</TableHead>
                  <TableHead>시간</TableHead>
                  <TableHead>대상</TableHead>
                  <TableHead>엔티티</TableHead>
                  <TableHead>Span 수</TableHead>
                  <TableHead>지연</TableHead>
                  <TableHead className="text-right">상세</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((row) => (
                  <TableRow key={row.request_id}>
                    <TableCell className="font-mono text-xs">{shortId(row.request_id)}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDateTime(row.created_at)}</TableCell>
                    <TableCell className="font-mono text-xs">{row.output_target}</TableCell>
                    <TableCell className="max-w-[280px] truncate text-xs">
                      {Object.keys(row.entity_counts).join(", ") || "-"}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{row.detected_span_count}</TableCell>
                    <TableCell className="font-mono text-xs">{formatMs(row.latency_ms)}</TableCell>
                    <TableCell className="text-right">
                      <Button type="button" size="sm" variant="outline" onClick={() => void openDetail(row.request_id)}>
                        열기
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {!filtered.length && (
                  <TableRow>
                    <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                      로그가 없습니다
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Sheet open={open} onOpenChange={handleSheetOpenChange}>
        <SheetContent className="w-full overflow-hidden p-0 sm:max-w-3xl">
          <SheetHeader className="border-b px-5 py-4">
            <SheetTitle className="font-mono text-sm">{detail ? shortId(detail.request_id) : "요청"}</SheetTitle>
            <SheetDescription>원문 요청 텍스트 없이 저장된 안전 감사 상세입니다.</SheetDescription>
          </SheetHeader>
          {detail && (
            <ScrollArea className="h-[calc(100vh-73px)]">
              <div className="space-y-4 p-5">
                <div className="grid gap-3 sm:grid-cols-4">
                  <div className="rounded-md border p-3">
                    <div className="text-xs text-muted-foreground">액션</div>
                    <div className="mt-2">
                      <StatusBadge value={detail.blocked ? "block" : "allow"} tone={detail.blocked ? "danger" : "success"} />
                    </div>
                  </div>
                  <div className="rounded-md border p-3">
                    <div className="text-xs text-muted-foreground">지연</div>
                    <div className="mt-2 font-mono text-sm">{formatMs(detail.latency_ms)}</div>
                  </div>
                  <div className="rounded-md border p-3">
                    <div className="text-xs text-muted-foreground">길이</div>
                    <div className="mt-2 font-mono text-sm">{detail.text_length}</div>
                  </div>
                  <div className="rounded-md border p-3">
                    <div className="text-xs text-muted-foreground">원문 로그</div>
                    <div className="mt-2">
                      <StatusBadge value={detail.encrypted_raw_available ? "암호화됨" : "없음"} tone={detail.encrypted_raw_available ? "success" : "muted"} />
                    </div>
                  </div>
                </div>
                {detail.encrypted_raw_available && (
                  <section className="space-y-3 rounded-md border p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h2 className="flex items-center gap-2 text-sm font-medium">
                        <KeyRound className="h-4 w-4 text-primary" />
                        원문 복호화
                      </h2>
                      <StatusBadge value={detail.encrypted_raw_key_hint ? `힌트: ${detail.encrypted_raw_key_hint}` : "키 힌트 없음"} tone="muted" />
                    </div>
                    <div className="flex flex-col gap-2 sm:flex-row">
                      <Input
                        type="password"
                        value={decryptKey}
                        onChange={(event) => setDecryptKey(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            void handleDecrypt()
                          }
                        }}
                        placeholder="복호화 키 입력"
                        className="h-9"
                      />
                      <Button type="button" onClick={() => void handleDecrypt()} disabled={decrypting || !decryptKey.trim()} className="gap-2">
                        {decrypting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Unlock className="h-4 w-4" />}
                        복호화
                      </Button>
                    </div>
                    {decryptError && (
                      <Alert variant="destructive">
                        <AlertTitle>복호화 실패</AlertTitle>
                        <AlertDescription>{decryptError}</AlertDescription>
                      </Alert>
                    )}
                    {decryptedText && (
                      <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded-md border bg-muted/30 p-3 font-mono text-sm">
                        {decryptedText}
                      </pre>
                    )}
                  </section>
                )}
                <section>
                  <h2 className="mb-2 text-sm font-medium">저장된 출력</h2>
                  <pre className="min-h-[96px] whitespace-pre-wrap rounded-md border bg-muted/30 p-3 font-mono text-sm">
                    {detail.masked_text ?? "BLOCKED"}
                  </pre>
                </section>
                <section>
                  <h2 className="mb-2 text-sm font-medium">공개 span</h2>
                  <SpanTable spans={detail.spans} />
                </section>
              </div>
            </ScrollArea>
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}

function readableError(err: unknown) {
  if (!(err instanceof Error)) {
    return "요청 실패"
  }
  try {
    const parsed = JSON.parse(err.message) as { detail?: unknown }
    if (typeof parsed.detail === "string") {
      return parsed.detail
    }
  } catch {
    // Keep the fetch wrapper's message when it is not a JSON error payload.
  }
  return err.message
}
