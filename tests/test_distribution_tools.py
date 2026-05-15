import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers import get_test_connector
from mcp_server.tools.distribution_tools import get_distribution_stats


def test_distribution_stats_fare_amount():
    connector = get_test_connector()
    result = get_distribution_stats(connector, "trips", "fare_amount")
    assert result["count"] == 3
    assert result["min"] < result["max"]
    assert result["mean"] is not None
    assert result["std"] is not None
    print("PASS test_distribution_stats_fare_amount")


def test_distribution_stats_keys():
    connector = get_test_connector()
    result = get_distribution_stats(connector, "trips", "fare_amount")
    for key in ("column", "mean", "std", "min", "max", "count", "z_score_threshold"):
        assert key in result, f"Missing key: {key}"
    print("PASS test_distribution_stats_keys")


if __name__ == "__main__":
    test_distribution_stats_fare_amount()
    test_distribution_stats_keys()
    print("All distribution tool tests passed.")
