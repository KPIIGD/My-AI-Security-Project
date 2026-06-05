import { Loader2, Play } from "lucide-react"
import { useState } from "react"

import { SpanTable } from "@/components/span-table"
import { StatusBadge } from "@/components/status-badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { traceGuardrail } from "@/lib/api"
import { formatMs } from "@/lib/format"
import type { TraceResponse } from "@/types"

const traceExample = "연락처는 공일공 일이삼사 오육칠팔입니다."

export function TracePage() {
  const [text, setText] = useState(traceExample)
  const [trace, setTrace] = useState<TraceResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleTrace() {
    setLoading(true)
    setError(null)
    try {
      setTrace(await traceGuardrail(text))
    } catch (err) {
      setError(err instanceof Error ? err.message : "추적 실패")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertTitle>추적 실패</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">추적 입력</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea value={text} onChange={(event) => setText(event.target.value)} className="min-h-[110px] font-mono" />
          <Button type="button" onClick={handleTrace} disabled={loading || !text.trim()} className="gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            추적 실행
          </Button>
        </CardContent>
      </Card>

      {trace && (
        <>
          <section className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-muted-foreground">지연</CardTitle>
              </CardHeader>
              <CardContent className="font-mono text-xl">{formatMs(trace.total_latency_ms)}</CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-muted-foreground">원문 길이</CardTitle>
              </CardHeader>
              <CardContent className="font-mono text-xl">{trace.raw_len}</CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-muted-foreground">정규화</CardTitle>
              </CardHeader>
              <CardContent>
                <StatusBadge value={trace.normalized_changed ? "변경됨" : "동일"} tone="muted" />
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-muted-foreground">감사 이벤트</CardTitle>
              </CardHeader>
              <CardContent className="font-mono text-xl">{trace.audit_event_count}</CardContent>
            </Card>
          </section>

          <div className="space-y-3">
            {trace.stages.map((stage) => (
              <Card key={`${stage.module}-${stage.title}`}>
                <CardHeader className="flex flex-row items-center justify-between gap-3">
                  <div>
                    <CardTitle className="text-sm">
                      <span className="mr-2 font-mono text-primary">{stage.module}</span>
                      {stage.title}
                    </CardTitle>
                    <p className="mt-1 text-xs text-muted-foreground">{stage.summary}</p>
                  </div>
                  <StatusBadge value={`${stage.span_count}개 span`} tone="muted" />
                </CardHeader>
                <CardContent className="space-y-3">
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    {stage.what_it_did.slice(0, 5).map((item, index) => (
                      <li key={`${stage.module}-${index}-${item}`}>{item}</li>
                    ))}
                  </ul>
                  {stage.spans.length ? (
                    <SpanTable spans={stage.spans} compact />
                  ) : (
                    <div className="rounded-md border px-3 py-6 text-center text-sm text-muted-foreground">
                      {emptyStageMessage(stage)}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function emptyStageMessage(stage: TraceResponse["stages"][number]): string {
  if (stage.module === "M1") {
    return "전처리 단계는 span을 직접 만들지 않고 정규화와 탐지용 variant만 생성합니다."
  }
  if (stage.module === "M8") {
    return "감사 이벤트가 없어서 저장 대상 span이 없습니다."
  }
  if (stage.module === "M7" && stage.title.includes("마스킹")) {
    return "마스킹 단계는 출력 문자열을 만들며 span 표는 정책 라우팅 단계에서 확인합니다."
  }
  return "이 단계에서 전달된 span이 없습니다."
}
