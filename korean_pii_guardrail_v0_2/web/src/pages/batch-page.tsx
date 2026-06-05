import { KeyRound, Loader2, Play } from "lucide-react"
import { useState } from "react"

import { MetricCard } from "@/components/metric-card"
import { StatusBadge } from "@/components/status-badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import { runBatch } from "@/lib/api"
import { compactNumber, formatMs, formatPercent, shortId } from "@/lib/format"
import type { BatchResponse } from "@/types"
import { Activity, Gauge, ShieldAlert, ShieldCheck } from "lucide-react"

const batchExample = [
  "연락처 010-1234-5678 입니다.",
  "메일은 test@example.com 입니다.",
  "고객명 홍길동, 연락처 010-9876-5432.",
  "오늘 날씨가 좋습니다.",
].join("\n")

interface BatchPageProps {
  logEncryptionKey: string
  logEncryptionHint: string
  onRefreshData: () => void
}

export function BatchPage({ logEncryptionKey, logEncryptionHint, onRefreshData }: BatchPageProps) {
  const [lines, setLines] = useState(batchExample)
  const [result, setResult] = useState<BatchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const trimmedLogKey = logEncryptionKey.trim()
  const logEncryptionReady = trimmedLogKey.length >= 8

  async function handleRun() {
    if (!logEncryptionReady) {
      setError("상단의 로그 암호화 키를 8자 이상 입력해야 새 배치 로그를 만들 수 있습니다.")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await runBatch({
        lines,
        encrypted_raw_logging_key: trimmedLogKey,
        encrypted_raw_key_hint: logEncryptionHint.trim() || undefined,
      })
      setResult(response)
      onRefreshData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "배치 실패")
    } finally {
      setLoading(false)
    }
  }

  const aggregate = result?.aggregate

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertTitle>배치 실패</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <CardTitle className="text-sm">배치 입력</CardTitle>
          <StatusBadge value={logEncryptionReady ? "자동 암호화" : "키 필요"} tone={logEncryptionReady ? "success" : "danger"} />
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea value={lines} onChange={(event) => setLines(event.target.value)} className="min-h-[180px] font-mono" />
          <div className="flex items-center gap-2 rounded-md border p-3 text-xs text-muted-foreground">
            <KeyRound className="h-4 w-4 shrink-0 text-primary" />
            상단 로그 암호화 키로 모든 새 배치 레코드 로그가 자동 암호화됩니다.
          </div>
          <Button type="button" onClick={handleRun} disabled={loading || !lines.trim()} className="gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            배치 분석
          </Button>
        </CardContent>
      </Card>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="레코드" value={compactNumber(result?.n ?? 0)} detail="처리됨" icon={Activity} />
        <MetricCard
          title="차단율"
          value={formatPercent(aggregate?.block_rate ?? 0)}
          detail={`${compactNumber(aggregate?.blocked_requests ?? 0)}건 차단`}
          icon={ShieldAlert}
        />
        <MetricCard
          title="Span 수"
          value={compactNumber(aggregate?.detected_span_count ?? 0)}
          detail={`${compactNumber(aggregate?.masked_span_count ?? 0)}개 마스킹`}
          icon={ShieldCheck}
        />
        <MetricCard
          title="평균 지연"
          value={formatMs(aggregate?.average_latency_ms ?? 0)}
          detail="레코드당"
          icon={Gauge}
        />
      </section>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">배치 레코드</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-hidden rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>요청</TableHead>
                  <TableHead>길이</TableHead>
                  <TableHead>Span 수</TableHead>
                  <TableHead>엔티티</TableHead>
                  <TableHead>액션</TableHead>
                  <TableHead>지연</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(result?.records ?? []).map((row) => (
                  <TableRow key={row.request_id}>
                    <TableCell className="font-mono text-xs">{row.idx}</TableCell>
                    <TableCell className="font-mono text-xs">{shortId(row.request_id)}</TableCell>
                    <TableCell className="font-mono text-xs">{row.text_length}</TableCell>
                    <TableCell className="font-mono text-xs">{row.detected_span_count}</TableCell>
                    <TableCell className="max-w-[280px] truncate text-xs">
                      {Object.keys(row.entity_counts).join(", ") || "-"}
                    </TableCell>
                    <TableCell>
                      <StatusBadge value={row.blocked ? "block" : "allow"} tone={row.blocked ? "danger" : "success"} />
                    </TableCell>
                    <TableCell className="font-mono text-xs">{formatMs(row.latency_ms)}</TableCell>
                  </TableRow>
                ))}
                {!result?.records.length && (
                  <TableRow>
                    <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                      레코드가 없습니다
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
