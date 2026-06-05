import {
  Activity,
  Database,
  FileUp,
  FolderInput,
  Loader2,
  Play,
  ShieldCheck,
  Square,
} from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import { MetricCard } from "@/components/metric-card"
import { SpanTable } from "@/components/span-table"
import { StatusBadge } from "@/components/status-badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  cancelDatasetRun,
  createDatasetRun,
  getDatasetRun,
  getDatasetRunRecords,
  getDatasetRuns,
  getDatasetSchema,
  registerLocalDataset,
  uploadDataset,
} from "@/lib/api"
import { compactNumber, formatDateTime, formatMs, shortId } from "@/lib/format"
import type {
  DatasetRegistration,
  DatasetRun,
  DatasetRunRecord,
  DatasetSchema,
  HealthPayload,
} from "@/types"

interface DatasetRunsPageProps {
  health: HealthPayload | null
}

type SourceMode = "upload" | "local"

const terminalStatuses = new Set(["completed", "failed", "cancelled"])

export function DatasetRunsPage({ health }: DatasetRunsPageProps) {
  const [sourceMode, setSourceMode] = useState<SourceMode>("upload")
  const [file, setFile] = useState<File | null>(null)
  const [localPath, setLocalPath] = useState("C:\\Users\\andyw\\Desktop\\M4_raw_staging")
  const [dataset, setDataset] = useState<DatasetRegistration | null>(null)
  const [schema, setSchema] = useState<DatasetSchema | null>(null)
  const [parserPreset, setParserPreset] = useState("generic_csv")
  const [textColumns, setTextColumns] = useState<string[]>([])
  const [idColumn, setIdColumn] = useState("none")
  const [rowLimit, setRowLimit] = useState(1000)
  const [runs, setRuns] = useState<DatasetRun[]>([])
  const [activeRun, setActiveRun] = useState<DatasetRun | null>(null)
  const [records, setRecords] = useState<DatasetRunRecord[]>([])
  const [selectedRecord, setSelectedRecord] = useState<DatasetRunRecord | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const realDataConfig = health?.real_data
  const progress = activeRun ? Math.min(100, (activeRun.records_processed / Math.max(activeRun.row_limit, 1)) * 100) : 0
  const latestRun = activeRun ?? runs[0] ?? null

  const refreshRuns = useCallback(async () => {
    setRuns(await getDatasetRuns(50))
  }, [])

  const loadRunRecords = useCallback(async (runId: string) => {
    setRecords(await getDatasetRunRecords(runId, 100))
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshRuns().catch((err: unknown) => setError(err instanceof Error ? err.message : "실행 목록 로드 실패"))
  }, [refreshRuns])

  useEffect(() => {
    if (!activeRun || terminalStatuses.has(activeRun.status)) {
      return
    }
    const timer = window.setInterval(() => {
      void getDatasetRun(activeRun.run_id)
        .then((nextRun) => {
          setActiveRun(nextRun)
          if (terminalStatuses.has(nextRun.status)) {
            void loadRunRecords(nextRun.run_id)
            void refreshRuns()
          }
        })
        .catch((err: unknown) => setError(err instanceof Error ? err.message : "실행 상태 갱신 실패"))
    }, 1000)
    return () => window.clearInterval(timer)
  }, [activeRun, loadRunRecords, refreshRuns])

  const selectedColumnSet = useMemo(() => new Set(textColumns), [textColumns])

  async function handleRegisterSource() {
    setLoading(true)
    setError(null)
    try {
      const nextDataset =
        sourceMode === "upload"
          ? await uploadDataset(assertFile(file))
          : await registerLocalDataset(localPath)
      const nextSchema = await getDatasetSchema(nextDataset.dataset_id)
      setDataset(nextDataset)
      setSchema(nextSchema)
      setParserPreset(nextSchema.parser_presets[0] ?? "generic_csv")
      setTextColumns(nextSchema.columns.slice(0, Math.min(3, nextSchema.columns.length)))
      setIdColumn("none")
    } catch (err) {
      setError(err instanceof Error ? err.message : "데이터셋 등록 실패")
    } finally {
      setLoading(false)
    }
  }

  async function handleStartRun() {
    if (!dataset || !schema) {
      return
    }
    setLoading(true)
    setError(null)
    try {
      const run = await createDatasetRun({
        dataset_id: dataset.dataset_id,
        parser_preset: parserPreset,
        text_columns: textColumns,
        id_column: idColumn === "none" ? null : idColumn,
        row_limit: rowLimit,
        retention_policy: "discard_after_run",
      })
      setActiveRun(run)
      setRecords([])
      void refreshRuns()
    } catch (err) {
      setError(err instanceof Error ? err.message : "데이터셋 실행 실패")
    } finally {
      setLoading(false)
    }
  }

  async function handleOpenRun(run: DatasetRun) {
    setActiveRun(run)
    await loadRunRecords(run.run_id)
  }

  async function handleCancelRun() {
    if (!activeRun) {
      return
    }
    const nextRun = await cancelDatasetRun(activeRun.run_id)
    setActiveRun(nextRun)
    void refreshRuns()
  }

  function toggleColumn(column: string) {
    setTextColumns((current) =>
      current.includes(column)
        ? current.filter((item) => item !== column)
        : [...current, column],
    )
  }

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertTitle>데이터셋 실행 불가</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="실제 NER"
          value={health?.ner_enabled ? "준비됨" : "필수"}
          detail={health?.ner_mode ?? "대기 중"}
          icon={Activity}
        />
        <MetricCard
          title="실행 수"
          value={compactNumber(runs.length)}
          detail={latestRun ? latestRun.status : "실행 없음"}
          icon={Database}
        />
        <MetricCard
          title="처리됨"
          value={compactNumber(latestRun?.records_processed ?? 0)}
          detail={`${compactNumber(latestRun?.detected_span_count ?? 0)}개 span`}
          icon={FileUp}
        />
        <MetricCard title="원문 보관" value="꺼짐" detail="실행 후 폐기만 허용" icon={ShieldCheck} />
      </section>

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">데이터 소스</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button
                type="button"
                variant={sourceMode === "upload" ? "secondary" : "outline"}
                className="gap-2"
                onClick={() => setSourceMode("upload")}
              >
                <FileUp className="h-4 w-4" />
                업로드
              </Button>
              <Button
                type="button"
                variant={sourceMode === "local" ? "secondary" : "outline"}
                className="gap-2"
                onClick={() => setSourceMode("local")}
              >
                <FolderInput className="h-4 w-4" />
                로컬 경로
              </Button>
            </div>

            {sourceMode === "upload" ? (
              <div className="space-y-2">
                <Label htmlFor="dataset-file">CSV, JSONL, TXT 또는 ZIP</Label>
                <Input
                  id="dataset-file"
                  type="file"
                  accept=".csv,.tsv,.jsonl,.txt,.zip"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                />
              </div>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="dataset-local-path">허용된 로컬 경로</Label>
                <Input
                  id="dataset-local-path"
                  value={localPath}
                  onChange={(event) => setLocalPath(event.target.value)}
                  className="font-mono"
                />
              </div>
            )}

            <Button type="button" onClick={handleRegisterSource} disabled={loading} className="gap-2">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FolderInput className="h-4 w-4" />}
              스키마 불러오기
            </Button>

            <Separator />

            <div className="space-y-2 text-xs text-muted-foreground">
              <div className="flex items-center justify-between gap-2">
                <span>허용 루트</span>
                <StatusBadge value={String(realDataConfig?.allowed_roots.length ?? 0)} tone="muted" />
              </div>
              <div className="truncate font-mono">{realDataConfig?.allowed_roots.join("; ") ?? "-"}</div>
              <div className="flex items-center justify-between gap-2">
                <span>암호화 보관</span>
                <StatusBadge value="비활성" tone="muted" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">스키마 매핑</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {schema ? (
              <>
                <div className="grid gap-3 md:grid-cols-3">
                  <InfoBox label="데이터셋" value={schema.display_name} />
                  <InfoBox label="유형" value={schema.file_type} />
                  <InfoBox label="행 수" value={compactNumber(schema.row_count_estimate)} />
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>파서 프리셋</Label>
                    <Select value={parserPreset} onValueChange={setParserPreset}>
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {schema.parser_presets.map((preset) => (
                          <SelectItem key={preset} value={preset}>
                            {preset}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>ID 컬럼</Label>
                    <Select value={idColumn} onValueChange={setIdColumn}>
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">없음</SelectItem>
                        {schema.columns.map((column) => (
                          <SelectItem key={column} value={column}>
                            {column}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>텍스트 컬럼</Label>
                  <div className="flex flex-wrap gap-2">
                    {schema.columns.length ? (
                      schema.columns.map((column) => (
                        <Button
                          key={column}
                          type="button"
                          size="sm"
                          variant={selectedColumnSet.has(column) ? "secondary" : "outline"}
                          onClick={() => toggleColumn(column)}
                        >
                          {column}
                        </Button>
                      ))
                    ) : (
                      <StatusBadge value="파서가 텍스트 필드 제공" tone="muted" />
                    )}
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-[180px_1fr]">
                  <div className="space-y-2">
                    <Label htmlFor="dataset-row-limit">행 제한</Label>
                    <Input
                      id="dataset-row-limit"
                      type="number"
                      min={1}
                      max={realDataConfig?.max_row_limit ?? 50000}
                      value={rowLimit}
                      onChange={(event) => setRowLimit(Number(event.target.value))}
                    />
                  </div>
                  <div className="rounded-md border p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs text-muted-foreground">보관 정책</span>
                      <StatusBadge value="실행 후 폐기" tone="success" />
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      암호화 보관은 접근 제어가 필요하므로 이 데모 콘솔에서는 비활성화되어 있습니다.
                    </div>
                  </div>
                </div>

                <Button type="button" onClick={handleStartRun} disabled={loading || !health?.ner_enabled} className="gap-2">
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  실행 시작
                </Button>
              </>
            ) : (
              <div className="rounded-md border px-3 py-12 text-center text-sm text-muted-foreground">
                컬럼을 매핑하려면 데이터셋 소스를 먼저 불러오세요.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {activeRun && (
        <Card>
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="text-sm">실행 모니터</CardTitle>
              <div className="mt-1 font-mono text-xs text-muted-foreground">{shortId(activeRun.run_id)}</div>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge value={activeRun.status} tone={activeRun.status === "failed" ? "danger" : activeRun.status === "completed" ? "success" : "muted"} />
              {!terminalStatuses.has(activeRun.status) && (
                <Button type="button" size="sm" variant="outline" onClick={() => void handleCancelRun()} className="gap-2">
                  <Square className="h-3.5 w-3.5" />
                  취소
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
            </div>
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard title="처리됨" value={compactNumber(activeRun.records_processed)} detail={`제한 ${compactNumber(activeRun.row_limit)}`} icon={Activity} />
              <MetricCard title="탐지 span" value={compactNumber(activeRun.detected_span_count)} detail={`${compactNumber(activeRun.masked_span_count)}개 마스킹`} icon={ShieldCheck} />
              <MetricCard title="차단" value={compactNumber(activeRun.blocked_count)} detail="레코드" icon={Database} />
              <MetricCard title="평균 지연" value={formatMs(activeRun.average_latency_ms)} detail={activeRun.ner_mode} icon={Loader2} />
            </section>
            {activeRun.error_code && (
              <Alert variant="destructive">
                <AlertTitle>{activeRun.error_code}</AlertTitle>
                <AlertDescription>{activeRun.error_message}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <RunsTable runs={runs} onOpenRun={(run) => void handleOpenRun(run)} />
        <RecordsTable records={records} onSelectRecord={setSelectedRecord} />
      </div>

      <Sheet open={selectedRecord !== null} onOpenChange={(open) => !open && setSelectedRecord(null)}>
        <SheetContent className="w-full overflow-hidden p-0 sm:max-w-3xl">
          <SheetHeader className="border-b px-5 py-4">
            <SheetTitle className="font-mono text-sm">
              {selectedRecord ? `row ${selectedRecord.row_index}` : "데이터셋 행"}
            </SheetTitle>
            <SheetDescription>원문 없는 데이터셋 레코드 상세입니다.</SheetDescription>
          </SheetHeader>
          {selectedRecord && (
            <ScrollArea className="h-[calc(100vh-73px)]">
              <div className="space-y-4 p-5">
                <div className="grid gap-3 sm:grid-cols-4">
                  <InfoBox label="행 해시" value={selectedRecord.row_id_hash} mono />
                  <InfoBox label="Span 수" value={String(selectedRecord.detected_span_count)} />
                  <InfoBox label="지연" value={formatMs(selectedRecord.latency_ms)} />
                  <InfoBox label="원문 로그" value="없음" />
                </div>
                <section>
                  <h2 className="mb-2 text-sm font-medium">안전 마스킹 요약</h2>
                  <pre className="min-h-[96px] whitespace-pre-wrap rounded-md border bg-muted/30 p-3 font-mono text-sm">
                    {selectedRecord.masked_text}
                  </pre>
                </section>
                <section>
                  <h2 className="mb-2 text-sm font-medium">공개 span</h2>
                  <SpanTable spans={selectedRecord.spans} />
                </section>
              </div>
            </ScrollArea>
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}

function assertFile(file: File | null): File {
  if (!file) {
    throw new Error("데이터셋 파일을 먼저 선택하세요")
  }
  return file
}

interface InfoBoxProps {
  label: string
  value: string
  mono?: boolean
}

function InfoBox({ label, value, mono = false }: InfoBoxProps) {
  return (
    <div className="rounded-md border p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={`mt-2 truncate text-sm ${mono ? "font-mono" : ""}`}>{value}</div>
    </div>
  )
}

interface RunsTableProps {
  runs: DatasetRun[]
  onOpenRun: (run: DatasetRun) => void
}

function RunsTable({ runs, onOpenRun }: RunsTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">최근 데이터셋 실행</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>실행</TableHead>
                <TableHead>상태</TableHead>
                <TableHead>행</TableHead>
                <TableHead>Span 수</TableHead>
                <TableHead className="text-right">열기</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.map((run) => (
                <TableRow key={run.run_id}>
                  <TableCell>
                    <div className="font-mono text-xs">{shortId(run.run_id)}</div>
                    <div className="mt-1 text-xs text-muted-foreground">{formatDateTime(run.created_at)}</div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge value={run.status} tone={run.status === "failed" ? "danger" : run.status === "completed" ? "success" : "muted"} />
                  </TableCell>
                  <TableCell className="font-mono text-xs">{run.records_processed}</TableCell>
                  <TableCell className="font-mono text-xs">{run.detected_span_count}</TableCell>
                  <TableCell className="text-right">
                    <Button type="button" size="sm" variant="outline" onClick={() => onOpenRun(run)}>
                      열기
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!runs.length && (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                    데이터셋 실행이 없습니다
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}

interface RecordsTableProps {
  records: DatasetRunRecord[]
  onSelectRecord: (record: DatasetRunRecord) => void
}

function RecordsTable({ records, onSelectRecord }: RecordsTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">실행 레코드</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>행 해시</TableHead>
                <TableHead>엔티티</TableHead>
                <TableHead>액션</TableHead>
                <TableHead>지연</TableHead>
                <TableHead className="text-right">상세</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {records.map((record) => (
                <TableRow key={`${record.run_id}-${record.row_index}`}>
                  <TableCell className="font-mono text-xs">{record.row_index}</TableCell>
                  <TableCell className="font-mono text-xs">{shortId(record.row_id_hash)}</TableCell>
                  <TableCell className="max-w-[240px] truncate text-xs">
                    {Object.keys(record.entity_counts).join(", ") || "-"}
                  </TableCell>
                  <TableCell>
                    <StatusBadge value={record.blocked ? "block" : "allow"} tone={record.blocked ? "danger" : "success"} />
                  </TableCell>
                  <TableCell className="font-mono text-xs">{formatMs(record.latency_ms)}</TableCell>
                  <TableCell className="text-right">
                    <Button type="button" size="sm" variant="outline" onClick={() => onSelectRecord(record)}>
                      열기
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!records.length && (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                    완료된 실행을 열어 안전한 행 요약을 확인하세요.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
