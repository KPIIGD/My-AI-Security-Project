import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import type { PublicSpan, TraceStageSpan } from "@/types"

import { StatusBadge } from "./status-badge"

interface SpanTableProps {
  spans: PublicSpan[] | TraceStageSpan[]
  compact?: boolean
}

export function SpanTable({ spans, compact = false }: SpanTableProps) {
  if (!spans.length) {
    return (
      <div className="rounded-md border px-3 py-6 text-center text-sm text-muted-foreground">
        탐지 span이 없습니다
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>유형</TableHead>
            <TableHead>위험도</TableHead>
            <TableHead>액션</TableHead>
            <TableHead>오프셋</TableHead>
            <TableHead>점수</TableHead>
            {!compact && <TableHead>탐지기</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {spans.map((span, index) => {
            const type = "entity_type" in span ? span.entity_type : span.type
            const risk = "risk_level" in span ? span.risk_level : span.risk
            const detectorIds = span.detector_ids ?? []
            return (
              <TableRow key={`${type}-${span.start}-${span.end}-${index}`}>
                <TableCell className="font-mono text-xs">{type}</TableCell>
                <TableCell>
                  <StatusBadge value={risk} tone={risk === "P0" ? "danger" : "default"} />
                </TableCell>
                <TableCell>
                  <StatusBadge
                    value={span.action}
                    tone={span.action === "block" ? "danger" : span.action === "mask" ? "success" : "muted"}
                  />
                </TableCell>
                <TableCell className="font-mono text-xs">
                  {span.start}:{span.end}
                </TableCell>
                <TableCell className="font-mono text-xs">{span.score.toFixed(3)}</TableCell>
                {!compact && (
                  <TableCell className="max-w-[260px] truncate font-mono text-xs text-muted-foreground">
                    {detectorIds.join(", ") || "-"}
                  </TableCell>
                )}
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
