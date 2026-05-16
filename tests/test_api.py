import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import duckdb
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def _make_tmp_db() -> str:
    """Create a temp DuckDB file with a trips table and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    os.unlink(tmp.name)  # DuckDB requires the path to not exist yet
    conn = duckdb.connect(tmp.name)
    conn.execute("""
        CREATE TABLE trips (
            trip_id     INTEGER,
            fare_amount FLOAT,
            vendor_id   VARCHAR,
            ingested_at TIMESTAMP
        )
    """)
    conn.execute("""
        INSERT INTO trips VALUES
        (1, 14.5, 'VTS', '2024-01-01 00:00:00'::TIMESTAMP),
        (2, 15.2, NULL,  '2024-01-02 00:00:00'::TIMESTAMP),
        (3, 13.8, 'CMT', '2024-01-03 00:00:00'::TIMESTAMP)
    """)
    conn.close()
    return tmp.name


def test_list_tables():
    db_path = _make_tmp_db()
    resp = client.get("/tables", params={"db_path": db_path})
    assert resp.status_code == 200
    data = resp.json()
    assert "tables" in data
    assert isinstance(data["tables"], list)
    assert len(data["tables"]) > 0
    print("PASS test_list_tables")


def test_run_check_returns_expected_keys():
    db_path = _make_tmp_db()
    resp = client.post("/check/trips", json={"db_type": "duckdb", "db_path": db_path})
    assert resp.status_code == 200
    data = resp.json()
    for key in ("schema", "null_rates", "row_count", "distribution_stats", "cardinality", "timestamp_gaps"):
        assert key in data, f"Missing key in check response: {key}"
    print("PASS test_run_check_returns_expected_keys")


def test_run_check_row_count():
    db_path = _make_tmp_db()
    resp = client.post("/check/trips", json={"db_type": "duckdb", "db_path": db_path})
    assert resp.status_code == 200
    assert resp.json()["row_count"]["total_rows"] == 3
    print("PASS test_run_check_row_count")


def test_run_check_null_rates_present_for_all_columns():
    db_path = _make_tmp_db()
    resp = client.post("/check/trips", json={"db_type": "duckdb", "db_path": db_path})
    schema = resp.json()["schema"]
    null_rates = resp.json()["null_rates"]
    for col in schema:
        assert col["column"] in null_rates, f"Missing null rate for column: {col['column']}"
    print("PASS test_run_check_null_rates_present_for_all_columns")


def test_get_report_404_when_missing():
    resp = client.get("/report/nonexistent_table")
    assert resp.status_code == 404
    print("PASS test_get_report_404_when_missing")


if __name__ == "__main__":
    test_list_tables()
    test_run_check_returns_expected_keys()
    test_run_check_row_count()
    test_run_check_null_rates_present_for_all_columns()
    test_get_report_404_when_missing()
    print("All API tests passed.")
