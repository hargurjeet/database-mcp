import json
from dotenv import load_dotenv
from fastmcp import FastMCP
from mcp_server.connectors.duckdb_connector import DuckDBConnector
from mcp_server.tools.schema_tools import get_schema
from mcp_server.tools.null_tools import check_null_rates
from mcp_server.tools.volume_tools import get_row_count
from mcp_server.tools.distribution_tools import get_distribution_stats
from mcp_server.tools.cardinality_tools import get_cardinality
from mcp_server.tools.timestamp_tools import detect_timestamp_gaps

load_dotenv()

mcp = FastMCP("generic-db-mcp")
_connector = None

_NUMERIC_TYPES = {"INTEGER", "FLOAT", "DOUBLE", "BIGINT", "DECIMAL"}
_STRING_TYPES  = {"VARCHAR", "TEXT", "STRING"}
_TIME_TYPES    = {"TIMESTAMP", "DATE"}


def _get_connector(config: dict):
    global _connector
    if _connector is None:
        db_type = config.get("db_type", "duckdb")
        if db_type == "duckdb":
            _connector = DuckDBConnector(config)
        else:
            raise ValueError(f"Unsupported db_type: {db_type}")
    return _connector


@mcp.tool()
def tool_list_tables(config_json: str) -> list[str]:
    config = json.loads(config_json)
    return _get_connector(config).list_tables()


@mcp.tool()
def tool_get_schema(config_json: str) -> list[dict]:
    config = json.loads(config_json)
    return get_schema(_get_connector(config), config["table"])


@mcp.tool()
def tool_check_null_rates(config_json: str) -> dict:
    config = json.loads(config_json)
    return check_null_rates(_get_connector(config), config["table"])


@mcp.tool()
def tool_get_row_count(config_json: str) -> dict:
    config = json.loads(config_json)
    return get_row_count(_get_connector(config), config["table"])


@mcp.tool()
def tool_get_distribution_stats(config_json: str, column: str) -> dict:
    config = json.loads(config_json)
    return get_distribution_stats(_get_connector(config), config["table"], column)


@mcp.tool()
def tool_get_cardinality(config_json: str, column: str) -> dict:
    config = json.loads(config_json)
    return get_cardinality(_get_connector(config), config["table"], column)


@mcp.tool()
def tool_detect_timestamp_gaps(config_json: str, column: str) -> dict:
    config = json.loads(config_json)
    return detect_timestamp_gaps(_get_connector(config), config["table"], column)


@mcp.tool()
def tool_run_full_check(config_json: str) -> dict:
    config = json.loads(config_json)
    connector = _get_connector(config)
    table = config["table"]
    schema = get_schema(connector, table)

    result = {
        "schema": schema,
        "null_rates": check_null_rates(connector, table),
        "row_count": get_row_count(connector, table),
        "distribution_stats": {},
        "cardinality": {},
        "timestamp_gaps": {},
    }

    for col in schema:
        name = col["column"]
        col_type = col["type"].upper()
        if any(t in col_type for t in _NUMERIC_TYPES):
            result["distribution_stats"][name] = get_distribution_stats(connector, table, name)
        if any(t in col_type for t in _STRING_TYPES):
            result["cardinality"][name] = get_cardinality(connector, table, name)
        if any(t in col_type for t in _TIME_TYPES):
            result["timestamp_gaps"][name] = detect_timestamp_gaps(connector, table, name)

    return result


if __name__ == "__main__":
    mcp.run()
