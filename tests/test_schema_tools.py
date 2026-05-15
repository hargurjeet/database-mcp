import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers import get_test_connector
from mcp_server.tools.schema_tools import get_schema


def test_schema_returns_all_columns():
    connector = get_test_connector()
    result = get_schema(connector, "trips")
    columns = [col["column"] for col in result]
    assert "trip_id" in columns
    assert "fare_amount" in columns
    assert "vendor_id" in columns
    assert "ingested_at" in columns
    print("PASS test_schema_returns_all_columns")


def test_schema_has_correct_types():
    connector = get_test_connector()
    result = get_schema(connector, "trips")
    type_map = {col["column"]: col["type"].upper() for col in result}
    assert "INTEGER" in type_map["trip_id"]
    assert "FLOAT" in type_map["fare_amount"]
    assert "VARCHAR" in type_map["vendor_id"]
    assert "TIMESTAMP" in type_map["ingested_at"]
    print("PASS test_schema_has_correct_types")


if __name__ == "__main__":
    test_schema_returns_all_columns()
    test_schema_has_correct_types()
    print("All schema tool tests passed.")
