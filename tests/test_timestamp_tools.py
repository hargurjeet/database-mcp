import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers import get_test_connector, get_test_connector_with_gaps
from mcp_server.tools.schema_tools import get_schema
from mcp_server.tools.timestamp_tools import detect_timestamp_gaps

TIME_TYPES = {"TIMESTAMP", "DATE"}


def _first_timestamp_column(connector, table: str) -> str:
    schema = get_schema(connector, table)
    for col in schema:
        if any(t in col["type"].upper() for t in TIME_TYPES):
            return col["column"]
    raise AssertionError(f"No timestamp column found in table {table}")


def test_gap_detection_returns_expected_keys():
    connector = get_test_connector()
    col = _first_timestamp_column(connector, "trips")
    result = detect_timestamp_gaps(connector, "trips", col)
    for key in ("column", "row_count", "min_ts", "max_ts",
                "median_gap_seconds", "max_gap_seconds",
                "large_gaps_detected", "large_gap_count"):
        assert key in result, f"Missing key: {key}"
    print("PASS test_gap_detection_returns_expected_keys")


def test_gap_detection_row_count_correct():
    connector = get_test_connector()
    col = _first_timestamp_column(connector, "trips")
    result = detect_timestamp_gaps(connector, "trips", col)
    assert result["row_count"] == 3
    print("PASS test_gap_detection_row_count_correct")


def test_gap_detection_max_greater_than_median():
    connector = get_test_connector()
    col = _first_timestamp_column(connector, "trips")
    result = detect_timestamp_gaps(connector, "trips", col)
    assert result["max_gap_seconds"] >= result["median_gap_seconds"]
    print("PASS test_gap_detection_max_greater_than_median")


def test_gap_detection_finds_large_gap():
    # 4 daily rows then one row 11 months later.
    # Median gap = 1 day; last gap ≈ 362 days → well above 10x threshold.
    connector = get_test_connector_with_gaps()
    col = _first_timestamp_column(connector, "trips")
    result = detect_timestamp_gaps(connector, "trips", col)
    assert result["large_gaps_detected"] is True, "Expected large gap to be detected"
    assert result["large_gap_count"] >= 1
    print("PASS test_gap_detection_finds_large_gap")


if __name__ == "__main__":
    test_gap_detection_returns_expected_keys()
    test_gap_detection_row_count_correct()
    test_gap_detection_max_greater_than_median()
    test_gap_detection_finds_large_gap()
    print("All timestamp tool tests passed.")
