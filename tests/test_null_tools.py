import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers import get_test_connector
from mcp_server.tools.null_tools import check_null_rates


def test_some_column_has_nulls():
    connector = get_test_connector()
    result = check_null_rates(connector, "trips")
    assert any(v > 0.0 for v in result.values()), "Expected at least one column with nulls"
    print("PASS test_some_column_has_nulls")


def test_some_column_fully_populated():
    connector = get_test_connector()
    result = check_null_rates(connector, "trips")
    assert any(v == 0.0 for v in result.values()), "Expected at least one fully populated column"
    print("PASS test_some_column_fully_populated")


def test_all_rates_in_valid_range():
    connector = get_test_connector()
    result = check_null_rates(connector, "trips")
    for col, rate in result.items():
        assert 0.0 <= rate <= 1.0, f"Null rate out of [0,1] for column {col}: {rate}"
    print("PASS test_all_rates_in_valid_range")


def test_result_covers_all_schema_columns():
    connector = get_test_connector()
    from mcp_server.tools.schema_tools import get_schema
    schema_cols = {c["column"] for c in get_schema(connector, "trips")}
    result_cols = set(check_null_rates(connector, "trips").keys())
    assert schema_cols == result_cols, f"Null rate result missing columns: {schema_cols - result_cols}"
    print("PASS test_result_covers_all_schema_columns")


if __name__ == "__main__":
    test_some_column_has_nulls()
    test_some_column_fully_populated()
    test_all_rates_in_valid_range()
    test_result_covers_all_schema_columns()
    print("All null tool tests passed.")
