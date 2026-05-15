# CLAUDE.md — Generic Database MCP Server

## What This Project Does

A generic MCP server that accepts a database config, auto-inspects the schema,
runs basic data quality checks, and uses Ollama (llama3.2 default, mixtral 7b optional)
to generate a natural language RCA report.

No hardcoded table names. No hardcoded column names.
The server figures everything out from the connection config alone.

---

## Architecture

```
User provides JSON config (db_type + connection details)
                │
                ▼
        DB Connector (DuckDB — Phase 1)
                │
                ▼
        Schema Introspector
        - lists all tables
        - detects column names + types
                │
                ▼
        Check Engine (auto-selects checks by column type)
        - FLOAT/INTEGER  → null rate, distribution stats, Z-score
        - VARCHAR        → null rate, cardinality, unexpected values
        - TIMESTAMP      → null rate, gaps, out-of-order records
        - ALL columns    → row count, completeness
                │
                ▼
        MCP Tools (execute checks via connector)
                │
                ▼
        Ollama ReAct Loop (llama3.2)
        - reads check results
        - calls tools for deeper drill-down if needed
        - generates RCA report
                │
                ▼
        RCA Report saved as JSON + Markdown
```

---

## Tech Stack

| Layer | Tool |
|-------|------|
| MCP Framework | FastMCP (Python) |
| Database Phase 1 | DuckDB |
| Database Phase 2 | PostgreSQL, MySQL (via connector abstraction) |
| LLM Default | Ollama llama3.2 |
| LLM Alternative | Ollama mixtral 7b |
| Testing | Plain Python scripts (python tests/test_*.py) |
| Language | Python 3.11+ |

---

## User Config — What Gets Passed In

```json
{
  "db_type": "duckdb",
  "db_path": "./data/warehouse.db",
  "table": "trips",
  "timestamp_column": "ingested_at"
}
```

`db_type` drives which connector is loaded.
`timestamp_column` is optional — used for gap and ordering checks if present.
Everything else is introspected automatically.

---

## Project Structure

```
generic-db-mcp/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── .env.example
│
├── mcp_server/
│   ├── server.py                   # FastMCP entrypoint + tool registration
│   ├── introspector.py             # Schema introspection + check selector
│   │
│   ├── connectors/
│   │   ├── base.py                 # Abstract base connector interface
│   │   └── duckdb_connector.py     # DuckDB implementation (Phase 1)
│   │
│   └── tools/
│       ├── schema_tools.py         # Schema snapshot, column type listing
│       ├── distribution_tools.py   # Z-score, basic distribution stats
│       ├── volume_tools.py         # Row counts, completeness
│       └── null_tools.py           # Null rate per column
│
├── agent/
│   ├── ollama_client.py            # Ollama API wrapper
│   ├── dispatcher.py               # ReAct loop
│   └── prompts.py                  # System prompt + tool definitions
│
├── data/
│   └── reports/                    # RCA reports saved here
│
└── tests/
    ├── helpers.py                  # Shared in-memory DuckDB setup
    ├── test_schema_tools.py        # python tests/test_schema_tools.py
    ├── test_distribution_tools.py
    ├── test_volume_tools.py
    └── test_null_tools.py
```

---

## DB Connector Abstraction

Tools never talk to DuckDB directly — they go through `BaseConnector`.
This is what makes Phase 2 (PostgreSQL, MySQL) possible with zero tool changes.

```python
# connectors/base.py
from abc import ABC, abstractmethod
import pandas as pd

class BaseConnector(ABC):

    @abstractmethod
    def execute(self, query: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_schema(self, table: str) -> list[dict]:
        pass

    @abstractmethod
    def close(self):
        pass
```

```python
# connectors/duckdb_connector.py
import duckdb
import pandas as pd
from .base import BaseConnector

class DuckDBConnector(BaseConnector):

    def __init__(self, config: dict):
        self.conn = duckdb.connect(config["db_path"])

    def execute(self, query: str) -> pd.DataFrame:
        return self.conn.execute(query).fetchdf()

    def get_schema(self, table: str) -> list[dict]:
        rows = self.conn.execute(f"DESCRIBE {table}").fetchall()
        return [{"column": r[0], "type": r[1]} for r in rows]

    def close(self):
        self.conn.close()
```

---

## Auto Check Selection

```python
# introspector.py

NUMERIC_TYPES = {"INTEGER", "FLOAT", "DOUBLE", "BIGINT", "DECIMAL"}
STRING_TYPES  = {"VARCHAR", "TEXT", "STRING"}
TIME_TYPES    = {"TIMESTAMP", "DATE"}

def select_checks(column: str, col_type: str) -> list[str]:
    checks = ["null_rate"]                          # always run

    if col_type.upper() in NUMERIC_TYPES:
        checks += ["distribution_stats", "z_score"]

    if col_type.upper() in STRING_TYPES:
        checks += ["cardinality", "unexpected_values"]

    if col_type.upper() in TIME_TYPES:
        checks += ["gap_detection", "ordering_check"]

    return checks
```

---

## MCP Tools

| Tool | Input | What It Does |
|------|-------|-------------|
| `get_schema(table)` | table name | Returns all columns + types |
| `check_null_rates(table)` | table name | Null % per column |
| `get_row_count(table)` | table name | Total + recent row counts |
| `get_distribution_stats(table, column)` | table, numeric column | Mean, std, min, max, Z-score |
| `get_cardinality(table, column)` | table, string column | Distinct value count + top values |
| `detect_timestamp_gaps(table, column)` | table, timestamp column | Finds missing time periods |
| `run_full_check(table)` | table name | Runs all applicable checks, returns summary dict |

---

## Ollama ReAct Loop

```python
# agent/dispatcher.py

import ollama
from mcp_server.tools import dispatch_tool, parse_tool_call, wants_tool_call

OLLAMA_MODEL = "llama3.2"   # override with mixtral for deeper reasoning

def run_rca(table: str, check_summary: dict) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": f"Table: {table}\nCheck results: {check_summary}"}
    ]

    while True:
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages)

        if wants_tool_call(response):
            tool_name, args = parse_tool_call(response)
            result = dispatch_tool(tool_name, args)
            messages.append({"role": "tool", "content": str(result)})
        else:
            return response["message"]["content"]   # final RCA narrative
```

---

## Testing — Plain Python Scripts

No pytest. Run each file directly with `python tests/test_*.py`.
All tests use an in-memory DuckDB instance set up in `helpers.py`.

```python
# tests/helpers.py
import duckdb
from mcp_server.connectors.duckdb_connector import DuckDBConnector

def get_test_connector():
    conn = duckdb.connect(":memory:")
    conn.execute("""
        CREATE TABLE trips (
            trip_id     INTEGER,
            fare_amount FLOAT,
            vendor_id   VARCHAR,
            ingested_at TIMESTAMP
        )
    """)
    conn.execute("""
        INSERT INTO trips VALUES
        (1, 14.5, 'VTS', NOW()),
        (2, 15.2, NULL,  NOW()),
        (3, 13.8, 'CMT', NOW())
    """)
    connector = DuckDBConnector.__new__(DuckDBConnector)
    connector.conn = conn
    return connector
```

```python
# tests/test_null_tools.py
from helpers import get_test_connector
from mcp_server.tools.null_tools import check_null_rates

def test_vendor_id_has_nulls():
    connector = get_test_connector()
    result = check_null_rates(connector, "trips")
    assert result["vendor_id"] > 0.0, "Expected non-zero null rate for vendor_id"
    print("PASS test_vendor_id_has_nulls")

def test_fare_amount_no_nulls():
    connector = get_test_connector()
    result = check_null_rates(connector, "trips")
    assert result["fare_amount"] == 0.0, "Expected zero null rate for fare_amount"
    print("PASS test_fare_amount_no_nulls")

if __name__ == "__main__":
    test_vendor_id_has_nulls()
    test_fare_amount_no_nulls()
    print("All null tool tests passed.")
```

Run with:
```bash
python tests/test_null_tools.py
```

---

## Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy environment file
cp .env.example .env

# 3. Start MCP server
python mcp_server/server.py

# 4. Run a quality check by passing config
python agent/dispatcher.py '{
  "db_type": "duckdb",
  "db_path": "./data/warehouse.db",
  "table": "trips",
  "timestamp_column": "ingested_at"
}'

# 5. Run tests
python tests/test_null_tools.py
python tests/test_schema_tools.py
python tests/test_distribution_tools.py
python tests/test_volume_tools.py
```

---

## Environment Variables

```bash
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
REPORTS_PATH=./data/reports/
```

---

## Roadmap

| Phase | Scope |
|-------|-------|
| Phase 1 | DuckDB connector, core tools, Ollama ReAct loop, plain Python tests |
| Phase 2 | PostgreSQL + MySQL connectors (no tool changes needed) |
| Phase 3 | Scheduled scans via Prefect |
| Phase 4 | REST API — POST config, GET report |
