# database-mcp

A generic MCP server that connects to a DuckDB database, auto-inspects the schema, runs data quality checks across every table and column, and uses a local Ollama LLM to generate a natural-language Root Cause Analysis (RCA) report.

No table names or column names are ever hardcoded. Everything is discovered at runtime from the connection config alone.

---

## Features

- **Auto-discovery** — pass connection details, the server lists all tables; pick one and it figures out every column and type
- **Type-aware checks** — numeric columns get distribution stats + Z-score thresholds; VARCHAR columns get cardinality + top values; TIMESTAMP columns get gap detection
- **Ollama ReAct loop** — `llama3.2` (default) iteratively calls tools to drill down, then writes a plain-English RCA report
- **MCP tools** — usable directly from any MCP client (Claude, etc.)
- **REST API** — thin FastAPI layer for programmatic access

---

## Stack

| Layer | Tool |
|-------|------|
| MCP framework | FastMCP |
| Database | DuckDB |
| LLM | Ollama (`llama3.2` default, `mistral:7b` optional) |
| REST API | FastAPI + Uvicorn |
| Tests | Plain Python scripts (`python tests/test_*.py`) |

---

## Installation

```bash
git clone https://github.com/hargurjeet/database-mcp.git
cd database-mcp

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

Ollama must be running locally:
```bash
ollama pull llama3.2
ollama serve
```

---

## Configuration

Edit `.env`:

```bash
OLLAMA_MODEL=llama3.2          # or mistral:7b
OLLAMA_BASE_URL=http://localhost:11434
REPORTS_PATH=./data/reports/
```

---

## Usage

### 1. MCP server

```bash
python mcp_server/server.py
```

Available tools:

| Tool | What it does |
|------|-------------|
| `tool_list_tables` | Lists all tables — call this first |
| `tool_get_schema` | Columns + types for a table |
| `tool_check_null_rates` | Null % per column |
| `tool_get_row_count` | Total row count |
| `tool_get_distribution_stats` | Mean / std / min / max for a numeric column |
| `tool_get_cardinality` | Distinct count + top values for a VARCHAR column |
| `tool_detect_timestamp_gaps` | Gap analysis for a TIMESTAMP column |
| `tool_run_full_check` | Runs all applicable checks — returns full summary |

All tools accept a `config_json` string:
```json
{"db_type": "duckdb", "db_path": "./data/warehouse.db", "table": "trips"}
```

`table` is only required for table-specific tools. `tool_list_tables` needs only the connection fields.

---

### 2. REST API

```bash
uvicorn api.main:app --reload
# Swagger UI at http://localhost:8000/docs
```

| Method | Endpoint | Body / Params | What it does |
|--------|----------|---------------|-------------|
| `GET` | `/tables` | `?db_path=./data/warehouse.db` | List all tables |
| `POST` | `/check/{table}` | `{"db_type":"duckdb","db_path":"..."}` | Full quality check, returns JSON |
| `POST` | `/rca/{table}` | `{"db_type":"duckdb","db_path":"..."}` | Full check + Ollama RCA, saves Markdown report |
| `GET` | `/report/{table}` | — | Retrieve last saved RCA report |

Example:
```bash
# List tables
curl "http://localhost:8000/tables?db_path=./data/warehouse.db"

# Run full quality check
curl -X POST http://localhost:8000/check/trips \
  -H "Content-Type: application/json" \
  -d '{"db_type":"duckdb","db_path":"./data/warehouse.db"}'

# Generate RCA report (requires Ollama)
curl -X POST http://localhost:8000/rca/trips \
  -H "Content-Type: application/json" \
  -d '{"db_type":"duckdb","db_path":"./data/warehouse.db"}'
```

---

### 3. Run the agent directly

```bash
python agent/dispatcher.py '{
  "db_type": "duckdb",
  "db_path": "./data/warehouse.db",
  "table": "trips"
}'
```

Report is printed to stdout and saved to `data/reports/trips_rca.md`.

---

## Tests

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

## Project structure

```
database-mcp/
├── api/
│   ├── main.py              # FastAPI app
│   └── routes.py            # Route handlers
│
├── mcp_server/
│   ├── server.py            # FastMCP entrypoint + tool registration
│   ├── introspector.py      # Schema → check plan mapping
│   ├── connectors/
│   │   ├── base.py          # Abstract connector interface
│   │   └── duckdb_connector.py
│   └── tools/
│       ├── schema_tools.py
│       ├── null_tools.py
│       ├── volume_tools.py
│       ├── distribution_tools.py
│       ├── cardinality_tools.py
│       └── timestamp_tools.py
│
├── agent/
│   ├── dispatcher.py        # Ollama ReAct loop
│   ├── ollama_client.py
│   └── prompts.py
│
├── data/reports/            # Saved RCA reports
├── docs/session_log.md      # Full development history
└── tests/
```

---

## Roadmap

| Phase | Status |
|-------|--------|
| Phase 1 — DuckDB + core tools + Ollama loop | Complete |
| Phase 2 — PostgreSQL / MySQL connectors | Skipped |
| Phase 3 — Prefect scheduled scans | Skipped |
| Phase 4 — REST API | Complete |
