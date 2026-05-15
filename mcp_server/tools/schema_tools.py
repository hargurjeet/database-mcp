from mcp_server.connectors.base import BaseConnector


def get_schema(connector: BaseConnector, table: str) -> list[dict]:
    return connector.get_schema(table)
