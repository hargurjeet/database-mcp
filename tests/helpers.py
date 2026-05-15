import duckdb
from mcp_server.connectors.duckdb_connector import DuckDBConnector


def get_test_connector():
    conn = duckdb.connect(":memory:")
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
        (1, 14.5, 'VTS', NOW()),
        (2, 15.2, NULL,  NOW()),
        (3, 13.8, 'CMT', NOW())
    """)
    connector = DuckDBConnector.__new__(DuckDBConnector)
    connector.conn = conn
    return connector
