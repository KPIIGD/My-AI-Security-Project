import { Activity, Gauge, ShieldAlert, ShieldCheck } from "lucide-react"
import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts"

import { MetricCard } from "@/components/metric-card"
import { StatusBadge } from "@/components/status-badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { countEntries, compactNumber, formatDateTime, formatMs, formatPercent, shortId } from "@/lib/format"
import type { HealthPayload, LogSummary, MetricsPayload } from "@/types"

interface OverviewPageProps {
  health: HealthPayload | null
  metrics: MetricsPayload | null
  logs: LogSummary[]
  loading: boolean
}

export function OverviewPage({ health, metrics, logs, loading }: OverviewPageProps) {
  const entityData = countEntries(metrics?.entity_counts ?? {}).slice(0, 8)
  const actionData = countEntries(metrics?.action_counts ?? {})
  const entityChartWidth = Math.max(560, entityData.length * 96)

  return (
    <div className="space-y-4">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="요청 수"
          value={compactNumber(metrics?.total_requests ?? 0)}
          detail={health?.status === "ok" ? "API 온라인" : loading ? "로딩 중" : "API 오프라인"}
          icon={Activity}
        />
        <MetricCard
          title="차단율"
          value={formatPercent(metrics?.block_rate ?? 0)}
          detail={`${compactNumber(metrics?.blocked_requests ?? 0)}건 차단`}
          icon={ShieldAlert}
        />
        <MetricCard
          title="마스킹 span"
          value={compactNumber(metrics?.masked_span_count ?? 0)}
          detail={`${compactNumber(metrics?.detected_span_count ?? 0)}개 탐지`}
          icon={ShieldCheck}
        />
        <MetricCard
          title="평균 지연"
          value={formatMs(metrics?.average_latency_ms ?? 0)}
          detail={health?.ner_mode ?? "대기 중"}
          icon={Gauge}
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">엔티티 분포</CardTitle>
          </CardHeader>
          <CardContent>
            {entityData.length ? (
              <div className="overflow-x-auto overflow-y-hidden">
                <BarChart width={entityChartWidth} height={280} data={entityData} margin={{ left: 0, right: 12 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-18} textAnchor="end" height={70} />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} width={36} />
                  <Tooltip
                    cursor={{ fill: "var(--muted)" }}
                    contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)" }}
                  />
                  <Bar dataKey="value" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </div>
            ) : (
              <div className="flex h-[280px] items-center justify-center text-sm text-muted-foreground">
                엔티티 데이터가 없습니다
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">액션 분포</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {actionData.length ? (
              actionData.map((item) => (
                <div key={item.name} className="flex items-center justify-between gap-3 rounded-md border px-3 py-2">
                  <StatusBadge value={item.name} tone={item.name === "block" ? "danger" : "default"} />
                  <span className="font-mono text-sm">{compactNumber(item.value)}</span>
                </div>
              ))
            ) : (
              <div className="rounded-md border px-3 py-10 text-center text-sm text-muted-foreground">
                액션 데이터가 없습니다
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">최근 요청</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-hidden rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>요청</TableHead>
                  <TableHead>시간</TableHead>
                  <TableHead>Span 수</TableHead>
                  <TableHead>액션</TableHead>
                  <TableHead>지연</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.slice(0, 8).map((row) => (
                  <TableRow key={row.request_id}>
                    <TableCell className="font-mono text-xs">{shortId(row.request_id)}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDateTime(row.created_at)}</TableCell>
                    <TableCell className="font-mono text-xs">{row.detected_span_count}</TableCell>
                    <TableCell>
                      <StatusBadge value={row.blocked ? "block" : "allow"} tone={row.blocked ? "danger" : "success"} />
                    </TableCell>
                    <TableCell className="font-mono text-xs">{formatMs(row.latency_ms)}</TableCell>
                  </TableRow>
                ))}
                {!logs.length && (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                      요청이 없습니다
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
