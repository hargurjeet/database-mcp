import json
from dotenv import load_dotenv
from fastmcp import FastMCP
from mcp_server.connectors.duckdb_connector import DuckDBConnector
from mcp_server.tools.schema_tools import get_schema
from mcp_server.tools.null_tools import check_null_rates
from mcp_server.tools.volume_tools import get_row_count
from mcp_server.tools.distribution_tools import get_distribution_stats
from mcp_server.introspector import introspect

load_dotenv()

mcp = FastMCP("generic-db-mcp")
_connector = None


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
def tool_run_full_check(config_json: str) -> dict:
    config = json.loads(config_json)
    connector = _get_connector(config)
    table = config["table"]
    return {
        "schema": get_schema(connector, table),
        "null_rates": check_null_rates(connector, table),
        "row_count": get_row_count(connector, table),
        "check_plan": introspect(connector, table),
    }


if __name__ == "__main__":
    mcp.run()
