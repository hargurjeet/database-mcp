import duckdb
from mcp_server.connectors.duckdb_connector import DuckDBConnector

_CREATE_TRIPS = """
    CREATE TABLE trips (
        trip_id     INTEGER,
        fare_amount FLOAT,
        vendor_id   VARCHAR,
        ingested_at TIMESTAMP
    )
"""


def get_test_connector():
    conn = duckdb.connect(":memory:")
    conn.execute(_CREATE_TRIPS)
    conn.execute("""
        INSERT INTO trips VALUES
        (1, 14.5, 'VTS', '2024-01-01 00:00:00'::TIMESTAMP),
        (2, 15.2, NULL,  '2024-01-02 00:00:00'::TIMESTAMP),
        (3, 13.8, 'CMT', '2024-01-03 00:00:00'::TIMESTAMP)
    """)
    connector = DuckDBConnector.__new__(DuckDBConnector)
    connector.conn = conn
    return connector


def get_test_connector_with_gaps():
    """Five daily rows followed by one row 11 months later — guarantees a detectable large gap."""
    conn = duckdb.connect(":memory:")
    conn.execute(_CREATE_TRIPS)
    conn.execute("""
        INSERT INTO trips VALUES
        (1, 14.5, 'VTS', '2024-01-01 00:00:00'::TIMESTAMP),
        (2, 15.2, NULL,  '2024-01-02 00:00:00'::TIMESTAMP),
        (3, 13.8, 'CMT', '2024-01-03 00:00:00'::TIMESTAMP),
        (4, 12.0, 'VTS', '2024-01-04 00:00:00'::TIMESTAMP),
        (5, 11.5, 'CMT', '2024-12-31 00:00:00'::TIMESTAMP)
    """)
    connector = DuckDBConnector.__new__(DuckDBConnector)
    connector.conn = conn
    return connector
