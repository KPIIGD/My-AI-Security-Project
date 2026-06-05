import { Database, Server, ShieldCheck, SlidersHorizontal } from "lucide-react"

import { MetricCard } from "@/components/metric-card"
import { StatusBadge } from "@/components/status-badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { compactNumber, formatMs } from "@/lib/format"
import type { HealthPayload, MetricsPayload } from "@/types"

interface SettingsPageProps {
  health: HealthPayload | null
  metrics: MetricsPayload | null
}

export function SettingsPage({ health, metrics }: SettingsPageProps) {
  return (
    <div className="space-y-4">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="API 상태" value={health?.status ?? "오프라인"} detail={health?.version ?? "알 수 없음"} icon={Server} />
        <MetricCard title="NER 모드" value={health?.ner_enabled ? "real" : "mock"} detail={health?.ner_mode ?? "대기 중"} icon={SlidersHorizontal} />
        <MetricCard title="DB 레코드" value={compactNumber(metrics?.total_requests ?? 0)} detail="SQLite 감사 메타데이터" icon={Database} />
        <MetricCard title="원문 보관" value="자동 암호화" detail="상단 세션 키 필요" icon={ShieldCheck} />
      </section>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">런타임</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <InfoRow label="버전" value={health?.version ?? "-"} />
            <InfoRow label="로드된 프로필" value={health?.loaded_profiles.join(", ") ?? "-"} />
            <InfoRow label="데이터베이스" value={health?.db_path ?? "-"} mono />
            <InfoRow label="평균 지연" value={formatMs(metrics?.average_latency_ms ?? 0)} />
            <InfoRow label="실제 데이터 허용 루트" value={health?.real_data?.allowed_roots.join("; ") ?? "-"} mono />
            <InfoRow label="데이터셋 행 제한" value={String(health?.real_data?.max_row_limit ?? "-")} />
            <InfoRow label="업로드 제한" value={`${Math.round((health?.real_data?.upload_max_bytes ?? 0) / 1024 / 1024)} MB`} />
          </div>
          <Separator />
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-md border p-3">
              <div className="text-xs text-muted-foreground">공개 span 원문 값</div>
              <div className="mt-2">
                <StatusBadge value="반환 안 함" tone="success" />
              </div>
            </div>
            <div className="rounded-md border p-3">
              <div className="text-xs text-muted-foreground">SQLite 평문 원문 값</div>
              <div className="mt-2">
                <StatusBadge value="저장 안 함" tone="success" />
              </div>
            </div>
            <div className="rounded-md border p-3">
              <div className="text-xs text-muted-foreground">암호화 원문 로그</div>
              <div className="mt-2">
                <StatusBadge value="세션 키로 자동" tone="muted" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

interface InfoRowProps {
  label: string
  value: string
  mono?: boolean
}

function InfoRow({ label, value, mono = false }: InfoRowProps) {
  return (
    <div className="rounded-md border p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={`mt-2 truncate text-sm ${mono ? "font-mono" : ""}`}>{value}</div>
    </div>
  )
}
