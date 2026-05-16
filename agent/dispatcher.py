import sys
import json
import os
import re
from dotenv import load_dotenv
from agent.prompts import SYSTEM_PROMPT
from agent.ollama_client import chat
from mcp_server.connectors.duckdb_connector import DuckDBConnector
from mcp_server.tools.schema_tools import get_schema
from mcp_server.tools.null_tools import check_null_rates
from mcp_server.tools.volume_tools import get_row_count
from mcp_server.tools.distribution_tools import get_distribution_stats
from mcp_server.tools.cardinality_tools import get_cardinality
from mcp_server.tools.timestamp_tools import detect_timestamp_gaps

load_dotenv()

REPORTS_PATH = os.getenv("REPORTS_PATH", "./data/reports/")

_TOOL_MAP = {
    "get_schema": get_schema,
    "check_null_rates": check_null_rates,
    "get_row_count": get_row_count,
    "get_distribution_stats": get_distribution_stats,
    "get_cardinality": get_cardinality,
    "detect_timestamp_gaps": detect_timestamp_gaps,
}


def _extract_tool_call(content: str) -> dict | None:
    """Return the first {\"tool\": ...} JSON object found in content, or None.

    Uses raw_decode so nested objects (e.g. \"args\": {\"table\": ...}) are handled
    correctly — a simple regex on {...} would miss the inner braces.
    """
    try:
        data = json.loads(content)
        if "tool" in data:
            return data
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    for match in re.finditer(r'\{', content):
        try:
            obj, _ = decoder.raw_decode(content, match.start())
            if isinstance(obj, dict) and "tool" in obj:
                return obj
        except json.JSONDecodeError:
            continue
    return None


def _wants_tool_call(response: dict) -> bool:
    return _extract_tool_call(response["message"]["content"]) is not None


def _parse_tool_call(response: dict) -> tuple[str, dict]:
    data = _extract_tool_call(response["message"]["content"])
    return data["tool"], data.get("args", {})


def run_rca(config: dict) -> str:
    connector = DuckDBConnector(config)
    table = config["table"]

    check_summary = {
        "schema": get_schema(connector, table),
        "null_rates": check_null_rates(connector, table),
        "row_count": get_row_count(connector, table),
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Table: {table}\nCheck results:\n{json.dumps(check_summary, indent=2)}"},
    ]

    while True:
        response = chat(messages)

        if _wants_tool_call(response):
            tool_name, args = _parse_tool_call(response)
            fn = _TOOL_MAP.get(tool_name)
            if fn is None:
                messages.append({"role": "tool", "content": f"Unknown tool: {tool_name}"})
                continue
            result = fn(connector, **args)
            messages.append({"role": "tool", "content": json.dumps(result)})
        else:
            return response["message"]["content"]


def save_report(table: str, report: str):
    os.makedirs(REPORTS_PATH, exist_ok=True)
    path = os.path.join(REPORTS_PATH, f"{table}_rca.md")
    with open(path, "w") as f:
        f.write(report)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    config = json.loads(sys.argv[1])
    report = run_rca(config)
    print(report)
    save_report(config["table"], report)
