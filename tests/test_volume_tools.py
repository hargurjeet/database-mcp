import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers import get_test_connector
from mcp_server.tools.volume_tools import get_row_count


def test_row_count():
    connector = get_test_connector()
    result = get_row_count(connector, "trips")
    assert result["total_rows"] == 3, f"Expected 3 rows, got {result['total_rows']}"
    assert result["table"] == "trips"
    print("PASS test_row_count")


if __name__ == "__main__":
    test_row_count()
    print("All volume tool tests passed.")
