import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers import get_test_connector
from mcp_server.tools.schema_tools import get_schema
from mcp_server.tools.cardinality_tools import get_cardinality

STRING_TYPES = {"VARCHAR", "TEXT", "STRING"}


def _first_string_column(connector, table: str) -> str:
    schema = get_schema(connector, table)
    for col in schema:
        if any(t in col["type"].upper() for t in STRING_TYPES):
            return col["column"]
    raise AssertionError(f"No string column found in table {table}")


def test_cardinality_returns_expected_keys():
    connector = get_test_connector()
    col = _first_string_column(connector, "trips")
    result = get_cardinality(connector, "trips", col)
    for key in ("column", "distinct_count", "top_values"):
        assert key in result, f"Missing key: {key}"
    print("PASS test_cardinality_returns_expected_keys")


def test_cardinality_distinct_count_positive():
    connector = get_test_connector()
    col = _first_string_column(connector, "trips")
    result = get_cardinality(connector, "trips", col)
    assert result["distinct_count"] >= 1
    print("PASS test_cardinality_distinct_count_positive")


def test_cardinality_top_values_structure():
    connector = get_test_connector()
    col = _first_string_column(connector, "trips")
    result = get_cardinality(connector, "trips", col)
    assert isinstance(result["top_values"], list)
    for entry in result["top_values"]:
        assert "value" in entry, f"Missing 'value' key in top_values entry: {entry}"
        assert "freq" in entry, f"Missing 'freq' key in top_values entry: {entry}"
    print("PASS test_cardinality_top_values_structure")


if __name__ == "__main__":
    test_cardinality_returns_expected_keys()
    test_cardinality_distinct_count_positive()
    test_cardinality_top_values_structure()
    print("All cardinality tool tests passed.")
