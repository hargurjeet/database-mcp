import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
