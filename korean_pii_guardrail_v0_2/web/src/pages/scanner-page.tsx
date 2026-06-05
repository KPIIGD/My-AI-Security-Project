import { Activity, KeyRound, Loader2, Play, RotateCcw, Shield, Timer } from "lucide-react"
import { useState } from "react"

import { LocalHighlight } from "@/components/local-highlight"
import { MetricCard } from "@/components/metric-card"
import { SpanTable } from "@/components/span-table"
import { StatusBadge } from "@/components/status-badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { applyGuardrail } from "@/lib/api"
import { formatMs } from "@/lib/format"
import type { ApplyResponse } from "@/types"

const exampleText = "고객명 홍길동, 연락처 010-1234-5678, 이메일 hong@example.com"

interface ScannerPageProps {
  result: ApplyResponse | null
  inputText: string
  logEncryptionKey: string
  logEncryptionHint: string
  onResult: (input: string, result: ApplyResponse) => void
  onRefreshData: () => void
}

export function ScannerPage({
  result,
  inputText,
  logEncryptionKey,
  logEncryptionHint,
  onResult,
  onRefreshData,
}: ScannerPageProps) {
  const [text, setText] = useState(inputText || exampleText)
  const [outputTarget, setOutputTarget] = useState("llm_input")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const trimmedLogKey = logEncryptionKey.trim()
  const logEncryptionReady = trimmedLogKey.length >= 8

  async function handleAnalyze() {
    if (!logEncryptionReady) {
      setError("상단의 로그 암호화 키를 8자 이상 입력해야 새 로그를 만들 수 있습니다.")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await applyGuardrail({
        text,
        output_target: outputTarget,
        encrypted_raw_logging_key: trimmedLogKey,
        encrypted_raw_key_hint: logEncryptionHint.trim() || undefined,
      })
      onResult(text, response)
      onRefreshData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "요청 실패")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertTitle>요청 실패</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-3">
            <CardTitle className="text-sm">입력</CardTitle>
            <Select value={outputTarget} onValueChange={setOutputTarget}>
              <SelectTrigger className="h-8 w-[160px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="llm_input">llm_input</SelectItem>
                <SelectItem value="external_output">external_output</SelectItem>
                <SelectItem value="audit_log">audit_log</SelectItem>
              </SelectContent>
            </Select>
          </CardHeader>
          <CardContent className="space-y-3">
            <Label htmlFor="scanner-input">텍스트</Label>
            <Textarea
              id="scanner-input"
              value={text}
              onChange={(event) => setText(event.target.value)}
              className="min-h-[180px] resize-y font-mono text-sm"
            />
            <div className="space-y-3 rounded-md border p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <KeyRound className="h-4 w-4 text-primary" />
                  암호화 원문 로그
                </div>
                <StatusBadge value={logEncryptionReady ? "자동 적용" : "키 필요"} tone={logEncryptionReady ? "success" : "danger"} />
              </div>
              <div className="text-xs text-muted-foreground">
                상단 로그 암호화 키로 모든 새 스캐너 로그가 자동 암호화됩니다. 키는 저장하지 않고 암호문만 감사 DB에 저장됩니다.
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" onClick={handleAnalyze} disabled={loading || !text.trim()} className="gap-2">
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                분석
              </Button>
              <Button type="button" variant="outline" onClick={() => setText(exampleText)} className="gap-2">
                <RotateCcw className="h-4 w-4" />
                예시
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-3">
            <CardTitle className="text-sm">로컬 상세</CardTitle>
            <StatusBadge value="브라우저에서만 원문 표시" tone="muted" />
          </CardHeader>
          <CardContent>
            <LocalHighlight text={result ? inputText : text} spans={result?.spans ?? []} />
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard
          title="탐지 span"
          value={`${result?.metrics.detected_span_count ?? 0}`}
          detail={`${result?.spans.length ?? 0}개 공개 span`}
          icon={Shield}
        />
        <MetricCard
          title="마스킹 span"
          value={`${result?.metrics.masked_span_count ?? 0}`}
          detail={result?.blocked ? "차단됨" : "마스킹 결과"}
          icon={Activity}
        />
        <MetricCard
          title="지연"
          value={formatMs(result?.metrics.latency_ms ?? 0)}
          detail={result?.request_id ?? "대기 중"}
          icon={Timer}
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">마스킹 결과</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="min-h-[140px] whitespace-pre-wrap rounded-md border bg-muted/30 p-3 font-mono text-sm leading-7">
              {result?.blocked ? "BLOCKED" : result?.masked_text ?? ""}
            </pre>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Span 상세</CardTitle>
          </CardHeader>
          <CardContent>
            <SpanTable spans={result?.spans ?? []} />
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
