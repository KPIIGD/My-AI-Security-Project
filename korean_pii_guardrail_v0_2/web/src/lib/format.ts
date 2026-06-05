export function compactNumber(value: number): string {
  return new Intl.NumberFormat("ko-KR", {
    notation: value >= 10_000 ? "compact" : "standard",
    maximumFractionDigits: value >= 10 ? 0 : 1,
  }).format(value)
}

export function formatMs(value: number): string {
  if (!Number.isFinite(value)) {
    return "0 ms"
  }
  return `${value.toFixed(value >= 100 ? 0 : 1)} ms`
}

export function formatPercent(value: number): string {
  if (!Number.isFinite(value)) {
    return "0%"
  }
  return `${(value * 100).toFixed(1)}%`
}

export function shortId(value: string): string {
  if (value.length <= 12) {
    return value
  }
  return `${value.slice(0, 8)}...${value.slice(-4)}`
}

export function formatDateTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat("ko-KR", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

export function countEntries(record: Record<string, number>): Array<{ name: string; value: number }> {
  return Object.entries(record)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
}
