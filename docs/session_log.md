# Session Log — database-mcp

## Project Goal
A generic MCP server that accepts database connection details, auto-inspects the schema,
runs data quality checks, and uses Ollama (llama3.2) to generate a natural language RCA report.
No hardcoded table or column names anywhere — everything is discovered at runtime.

---

## Phase 1 — COMPLETE (committed: fd277df)

### What was built
| File | Purpose |
|------|---------|
| `mcp_server/connectors/base.py` | Abstract `BaseConnector` with `execute`, `list_tables`, `get_schema`, `close` |
| `mcp_server/connectors/duckdb_connector.py` | DuckDB implementation (`SHOW TABLES`, `DESCRIBE`, `fetchdf`) |
| `mcp_server/introspector.py` | Maps each column type → list of applicable checks |
| `mcp_server/tools/schema_tools.py` | `get_schema(connector, table)` |
| `mcp_server/tools/null_tools.py` | `check_null_rates(connector, table)` — null % per column |
| `mcp_server/tools/volume_tools.py` | `get_row_count(connector, table)` |
| `mcp_server/tools/distribution_tools.py` | `get_distribution_stats(connector, table, column)` — mean, std, min, max, z_score_threshold |
| `mcp_server/tools/cardinality_tools.py` | `get_cardinality(connector, table, column)` — distinct count + top 10 values for VARCHAR |
| `mcp_server/tools/timestamp_tools.py` | `detect_timestamp_gaps(connector, table, column)` — median/max gap, flags gaps > 10× median |
| `mcp_server/server.py` | FastMCP server — 8 registered tools (see below) |
| `agent/ollama_client.py` | Thin wrapper around `ollama.chat`, model from `OLLAMA_MODEL` env var |
| `agent/prompts.py` | System prompt for Ollama ReAct loop |
| `agent/dispatcher.py` | ReAct loop — runs initial check, calls tools iteratively, saves RCA report as Markdown |

### MCP Tools registered
| Tool | What it does |
|------|-------------|
| `tool_list_tables` | Lists all tables in the DB — call this first, no table name needed |
| `tool_get_schema` | Returns columns + types for a table |
| `tool_check_null_rates` | Null % per column |
| `tool_get_row_count` | Total row count |
| `tool_get_distribution_stats` | Mean/std/min/max for a numeric column |
| `tool_get_cardinality` | Distinct count + top values for a VARCHAR column |
| `tool_detect_timestamp_gaps` | Gap analysis for a TIMESTAMP column |
| `tool_run_full_check` | Runs all applicable checks per column type, returns full summary dict |

### Intended usage flow
1. Pass connection config (no table name needed): `{"db_type": "duckdb", "db_path": "./data/warehouse.db"}`
2. Call `tool_list_tables` → returns list of table names
3. User picks a table
4. Call `tool_run_full_check` with config + chosen table → full quality report
5. Or call individual tools for targeted checks

### Tests — 18 passing
```
tests/test_null_tools.py          4 tests
tests/test_schema_tools.py        3 tests
tests/test_distribution_tools.py  2 tests
tests/test_volume_tools.py        1 test
tests/test_cardinality_tools.py   3 tests
tests/test_timestamp_tools.py     4 tests (uses get_test_connector_with_gaps() fixture)
```
Run with: `python tests/test_<name>.py`

### Key design rules enforced
- Tools never reference column names — always introspect schema first
- Test assertions never index into results by column name
- `tool_run_full_check` auto-dispatches by column type using `_NUMERIC_TYPES`, `_STRING_TYPES`, `_TIME_TYPES`

---

## Phase 2 — SKIPPED
PostgreSQL and MySQL connectors — skipped by user decision. DuckDB is sufficient for now.

## Phase 3 — SKIPPED
Prefect scheduled scans — skipped by user decision.

---

## Phase 4 — REST API (COMPLETE, commits 90ca572, 7849d5d)

### Additional fix — dispatcher tool-call extraction
Replaced regex `[^{}]` with `json.JSONDecoder.raw_decode` to correctly extract
JSON tool calls embedded in LLM prose. Regex failed on nested braces like
`"args": {"table": "trips"}`. End-to-end Ollama pipeline verified with llama3.2.

---

## Phase 5 — Next.js Frontend (COMPLETE)

### Goal
Thin FastAPI layer on top of the existing MCP tools.

### Endpoints planned
| Method | Path | What it does |
|--------|------|-------------|
| `GET` | `/tables` | Lists all tables in the connected DB |
| `POST` | `/check/{table}` | Runs full quality check on a table, returns JSON summary |
| `POST` | `/rca/{table}` | Runs full check + Ollama RCA, saves and returns Markdown report |
| `GET` | `/report/{table}` | Returns the last saved RCA report for a table |

### Config
Connection config passed as request body JSON (same shape as MCP tools).

### Files to create
- `api/main.py` — FastAPI app
- `api/routes.py` — route handlers
- `requirements.txt` — add `fastapi`, `uvicorn`

---

## Phase 5 — Next.js Frontend (COMPLETE)

### Files created
- `frontend/app/page.tsx` — 3-step state machine (Upload → Select Table → Results)
- `frontend/components/FileUpload.tsx` — drag-and-drop .db file upload, validates .db extension
- `frontend/components/TableSelector.tsx` — lists discovered tables as clickable cards
- `frontend/components/ResultsDashboard.tsx` — full results dashboard:
  - Summary cards (rows, columns, columns with nulls)
  - Schema table with inline null %
  - Horizontal bar chart for null rates (Recharts, green=clean, amber=has nulls)
  - Distribution stat cards for numeric columns
  - Cardinality tables for VARCHAR columns
  - Timestamp gap alerts (amber highlight if large gaps detected)

### FastAPI changes for frontend
- Added CORS middleware (`allow_origins=["http://localhost:3000"]`) to `api/main.py`
- Added `POST /upload` endpoint to `api/routes.py` — saves .db file to `data/uploads/`
- Added `python-multipart>=0.0.9` to `requirements.txt`

### How to run
```bash
# Terminal 1 — FastAPI backend
source .venv/bin/activate && uvicorn api.main:app --reload

# Terminal 2 — Next.js frontend
cd frontend && npm run dev
# Open http://localhost:3000
```

---

## Environment
- Python 3.14 — `.venv` at project root
- Node 25.9.0 — frontend dependencies in `frontend/node_modules`
- GitHub: https://github.com/hargurjeet/database-mcp
- Ollama running locally with llama3.2 and mistral:7b available

---

## Decisions & constraints
- No Postgres/MySQL (Phase 2 skipped)
- No Prefect (Phase 3 skipped)
- No pytest — plain `python tests/test_*.py`
- No hardcoded table or column names anywhere in source or tests
- Phase-by-phase: implement one phase, stop for user to test before proceeding
- Frontend uses file upload (not path input) — better UX, files saved to data/uploads/
