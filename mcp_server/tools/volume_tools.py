from mcp_server.connectors.base import BaseConnector


def get_row_count(connector: BaseConnector, table: str) -> dict:
    df = connector.execute(f"SELECT COUNT(*) AS total FROM {table}")
    return {"table": table, "total_rows": int(df["total"].iloc[0])}
