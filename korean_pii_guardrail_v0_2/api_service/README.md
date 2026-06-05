# Local Console API

FastAPI wrapper for the Korean PII Guardrail product console.

```powershell
cd korean_pii_guardrail_v0_2
python -m pip install -e .[dev,web]
$env:KPG_ALLOW_MOCK_NER = "1"
uvicorn api_service.app:app --host 127.0.0.1 --port 8000
```

Environment:

- `KPG_CONSOLE_DB`: SQLite path. Default is `data/console/audit.sqlite3`.
- `KPG_USE_REAL_NER=1`: attempt the finetuned NER path.
- `KPG_ALLOW_MOCK_NER=1`: allow mock fallback when real NER is unavailable.
- `KPG_REAL_DATA_ROOTS`: semicolon-separated local roots allowed for Dataset Runs.

The API stores SQLite audit metadata only. Raw request text and raw span text are not persisted.
Dataset Runs require real NER and persist only raw-free row summaries, public span metadata,
hashes, and aggregate counts. Raw retention is disabled in the unauthenticated demo shell.
