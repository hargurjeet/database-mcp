import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers import get_test_connector
from mcp_server.tools.schema_tools import get_schema
from mcp_server.tools.distribution_tools import get_distribution_stats

NUMERIC_TYPES = {"INTEGER", "FLOAT", "DOUBLE", "BIGINT", "DECIMAL"}


def _first_numeric_column(connector, table: str) -> str:
    schema = get_schema(connector, table)
    for col in schema:
        if any(t in col["type"].upper() for t in NUMERIC_TYPES):
            return col["column"]
    raise AssertionError(f"No numeric column found in table {table}")


def test_distribution_stats_numeric_column():
    connector = get_test_connector()
    col = _first_numeric_column(connector, "trips")
    result = get_distribution_stats(connector, "trips", col)
    assert result["count"] > 0
    assert result["min"] <= result["max"]
    assert result["mean"] is not None
    assert result["std"] is not None
    print(f"PASS test_distribution_stats_numeric_column (column: {col})")


def test_distribution_stats_keys():
    connector = get_test_connector()
    col = _first_numeric_column(connector, "trips")
    result = get_distribution_stats(connector, "trips", col)
    for key in ("column", "mean", "std", "min", "max", "count", "z_score_threshold"):
        assert key in result, f"Missing key: {key}"
    print("PASS test_distribution_stats_keys")


if __name__ == "__main__":
    test_distribution_stats_numeric_column()
    test_distribution_stats_keys()
    print("All distribution tool tests passed.")
