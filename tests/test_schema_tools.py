import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers import get_test_connector
from mcp_server.tools.schema_tools import get_schema


def test_schema_returns_list_of_dicts():
    connector = get_test_connector()
    result = get_schema(connector, "trips")
    assert isinstance(result, list)
    assert len(result) > 0
    print("PASS test_schema_returns_list_of_dicts")


def test_schema_each_entry_has_column_and_type():
    connector = get_test_connector()
    result = get_schema(connector, "trips")
    for entry in result:
        assert "column" in entry, f"Missing 'column' key in {entry}"
        assert "type" in entry, f"Missing 'type' key in {entry}"
        assert isinstance(entry["column"], str)
        assert isinstance(entry["type"], str)
    print("PASS test_schema_each_entry_has_column_and_type")


def test_list_tables_returns_known_table():
    connector = get_test_connector()
    tables = connector.list_tables()
    assert isinstance(tables, list)
    assert len(tables) > 0, "Expected at least one table"
    assert all(isinstance(t, str) for t in tables), "All table names should be strings"
    print("PASS test_list_tables_returns_known_table")


if __name__ == "__main__":
    test_schema_returns_list_of_dicts()
    test_schema_each_entry_has_column_and_type()
    test_list_tables_returns_known_table()
    print("All schema tool tests passed.")
