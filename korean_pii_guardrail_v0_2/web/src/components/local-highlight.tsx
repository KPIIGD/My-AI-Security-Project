import type { PublicSpan } from "@/types"

const colorByEntity: Record<string, string> = {
  PERSON_NAME: "border-amber-400/70 bg-amber-950/80 text-amber-50 shadow-amber-950/40",
  PHONE_MOBILE: "border-cyan-400/70 bg-cyan-950/80 text-cyan-50 shadow-cyan-950/40",
  PHONE_LANDLINE: "border-cyan-400/70 bg-cyan-950/80 text-cyan-50 shadow-cyan-950/40",
  EMAIL: "border-emerald-400/70 bg-emerald-950/80 text-emerald-50 shadow-emerald-950/40",
  ADDRESS_FULL: "border-sky-400/70 bg-sky-950/80 text-sky-50 shadow-sky-950/40",
  RRN: "border-red-400/70 bg-red-950/80 text-red-50 shadow-red-950/40",
  CREDIT_CARD: "border-red-400/70 bg-red-950/80 text-red-50 shadow-red-950/40",
  BANK_ACCOUNT: "border-violet-400/70 bg-violet-950/80 text-violet-50 shadow-violet-950/40",
  ORGANIZATION: "border-teal-400/70 bg-teal-950/80 text-teal-50 shadow-teal-950/40",
}

interface LocalHighlightProps {
  text: string
  spans: PublicSpan[]
}

export function LocalHighlight({ text, spans }: LocalHighlightProps) {
  const sorted = [...spans].sort((a, b) => a.start - b.start)
  const nodes: React.ReactNode[] = []
  let cursor = 0

  sorted.forEach((span) => {
    if (span.start > cursor) {
      nodes.push(<span key={`plain-${cursor}`}>{text.slice(cursor, span.start)}</span>)
    }
    const className = colorByEntity[span.entity_type] ?? "border-border bg-muted text-foreground shadow-black/20"
    nodes.push(
      <mark
        key={`${span.entity_type}-${span.start}-${span.end}`}
        className={`box-decoration-clone rounded border px-1 py-0.5 font-semibold shadow-sm ${className}`}
        title={`${span.entity_type} ${span.action}`}
      >
        {text.slice(span.start, span.end)}
      </mark>,
    )
    cursor = Math.max(cursor, span.end)
  })

  if (cursor < text.length) {
    nodes.push(<span key={`plain-${cursor}`}>{text.slice(cursor)}</span>)
  }

  return (
    <pre className="min-h-[120px] whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-left text-sm leading-7">
      {nodes.length ? nodes : text}
    </pre>
  )
}
