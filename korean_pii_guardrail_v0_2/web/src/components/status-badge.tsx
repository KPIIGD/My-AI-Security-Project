import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface StatusBadgeProps {
  value: string
  tone?: "default" | "danger" | "muted" | "success"
}

export function StatusBadge({ value, tone = "default" }: StatusBadgeProps) {
  return (
    <Badge
      variant={tone === "danger" ? "destructive" : tone === "muted" ? "secondary" : "outline"}
      className={cn(
        "whitespace-nowrap font-mono text-[11px]",
        tone === "success" && "border-primary/40 bg-primary/10 text-primary",
      )}
    >
      {value}
    </Badge>
  )
}
