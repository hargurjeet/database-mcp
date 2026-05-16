# CLAUDE.md — Generic Database MCP Server

## What This Project Does

A generic MCP server that accepts a DuckDB connection, auto-inspects the schema,
runs data quality checks on every table and column, and uses Ollama (llama3.2) to
generate a natural language RCA report.

**No hardcoded table names or column names anywhere.** Everything is discovered at runtime.

Full development history: `docs/session_log.md`

---

## Project Structure

```
database-mcp/
├── mcp_server/
│   ├── server.py                    # FastMCP entrypoint — 8 registered tools
│   ├── introspector.py              # Schema → check plan mapping
│   ├── connectors/
│   │   ├── base.py                  # Abstract BaseConnector (execute, list_tables, get_schema, close)
│   │   └── duckdb_connector.py      # DuckDB implementation
│   └── tools/
│       ├── schema_tools.py          # get_schema
│       ├── null_tools.py            # check_null_rates
│       ├── volume_tools.py          # get_row_count
│       ├── distribution_tools.py    # get_distribution_stats (numeric cols)
│       ├── cardinality_tools.py     # get_cardinality (VARCHAR cols)
│       └── timestamp_tools.py       # detect_timestamp_gaps (TIMESTAMP cols)
│
├── agent/
│   ├── dispatcher.py               # Ollama ReAct loop — runs checks, calls tools, saves report
│   ├── ollama_client.py            # Thin wrapper around ollama.chat
│   └── prompts.py                  # System prompt for RCA agent
│
├── api/
│   ├── main.py                     # FastAPI app + CORS (allows localhost:3000)
│   └── routes.py                   # POST /upload, GET /tables, POST /check/{table},
│                                   # POST /rca/{table}, GET /report/{table}
│
├── frontend/                       # Next.js 14 + Tailwind + Recharts UI
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                # 3-step flow: Upload → Select Table → Results
│   │   └── globals.css
│   ├── components/
│   │   ├── FileUpload.tsx          # Drag-and-drop .db file upload
│   │   ├── TableSelector.tsx       # List of discovered tables
│   │   └── ResultsDashboard.tsx    # Full results: schema, null rates chart,
│   │                               # distribution cards, cardinality, gap alerts
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   └── .env.local                  # NEXT_PUBLIC_API_URL=http://localhost:8000
│
├── tests/
│   ├── helpers.py                  # In-memory DuckDB fixtures (get_test_connector,
│   │                               # get_test_connector_with_gaps)
│   ├── test_null_tools.py          # 4 tests
│   ├── test_schema_tools.py        # 3 tests
│   ├── test_distribution_tools.py  # 2 tests
│   ├── test_volume_tools.py        # 1 test
│   ├── test_cardinality_tools.py   # 3 tests
│   ├── test_timestamp_tools.py     # 4 tests
│   └── test_api.py                 # 5 tests (FastAPI TestClient)
│
├── data/
│   ├── warehouse.db                # Sample DuckDB file for local testing
│   ├── uploads/                    # Uploaded .db files from frontend
│   └── reports/                    # Saved RCA Markdown reports
│
└── docs/
    └── session_log.md              # Full development history, decisions, phase status
```

---

## MCP Tools (registered in server.py)

| Tool | Input | What It Does |
|------|-------|-------------|
| `tool_list_tables` | connection config (no table needed) | Lists all tables — call this first |
| `tool_get_schema` | config + table | Columns + types |
| `tool_check_null_rates` | config + table | Null % per column |
| `tool_get_row_count` | config + table | Total rows |
| `tool_get_distribution_stats` | config + table + column | Mean/std/min/max for numeric |
| `tool_get_cardinality` | config + table + column | Distinct count + top values for VARCHAR |
| `tool_detect_timestamp_gaps` | config + table + column | Gap analysis for TIMESTAMP |
| `tool_run_full_check` | config + table | All applicable checks auto-dispatched by type |

Config shape: `{"db_type": "duckdb", "db_path": "./data/warehouse.db", "table": "trips"}`

---

## REST API Endpoints (api/routes.py)

| Method | Path | What It Does |
|--------|------|-------------|
| `POST` | `/upload` | Accepts .db file, saves to data/uploads/, returns db_path |
| `GET` | `/tables?db_path=...` | Lists all tables |
| `POST` | `/check/{table}` | Full quality check, returns JSON |
| `POST` | `/rca/{table}` | Full check + Ollama RCA, saves Markdown report |
| `GET` | `/report/{table}` | Returns last saved report |

---

## Running Locally

### Backend (FastAPI)
```bash
source .venv/bin/activate
uvicorn api.main:app --reload
# Swagger at http://localhost:8000/docs
```

### Frontend (Next.js)
```bash
cd frontend
npm run dev
# App at http://localhost:3000
```

### MCP Inspector
```bash
fastmcp dev inspector mcp_server/server.py
```

### Ollama RCA agent (direct)
```bash
PYTHONPATH=. python agent/dispatcher.py '{
  "db_type": "duckdb",
  "db_path": "./data/warehouse.db",
  "table": "trips"
}'
```

---

## Tests

No pytest. Run each file directly:

```bash
python tests/test_null_tools.py
python tests/test_schema_tools.py
python tests/test_distribution_tools.py
python tests/test_volume_tools.py
python tests/test_cardinality_tools.py
python tests/test_timestamp_tools.py
python tests/test_api.py
```

23 tests total. All use in-memory DuckDB — no external dependencies required.

---

## Environment Variables (.env)

```bash
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
REPORTS_PATH=./data/reports/
```

---

## Key Design Rules

- Tools never reference column names — always introspect schema first
- Test assertions never index results by column name
- `tool_run_full_check` auto-dispatches by column type using type-set constants
- Ollama dispatcher uses `json.JSONDecoder.raw_decode` to extract tool calls
  from mixed prose+JSON LLM responses (regex fails on nested braces)

---

## Phase Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 — DuckDB + core tools + Ollama loop | ✅ Complete | 23 tests passing |
| Phase 2 — PostgreSQL / MySQL connectors | ⏭ Skipped | User decision |
| Phase 3 — Prefect scheduled scans | ⏭ Skipped | User decision |
| Phase 4 — REST API | ✅ Complete | 5 endpoints + file upload |
| Phase 5 — Next.js frontend | ✅ Complete | Drag-drop upload, charts, 3-step flow |
