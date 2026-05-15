from mcp_server.connectors.base import BaseConnector


def check_null_rates(connector: BaseConnector, table: str) -> dict[str, float]:
    schema = connector.get_schema(table)
    total_df = connector.execute(f"SELECT COUNT(*) AS n FROM {table}")
    total = int(total_df["n"].iloc[0])

    if total == 0:
        return {col["column"]: 0.0 for col in schema}

    rates = {}
    for col in schema:
        name = col["column"]
        null_df = connector.execute(
            f"SELECT COUNT(*) AS n FROM {table} WHERE {name} IS NULL"
        )
        rates[name] = round(int(null_df["n"].iloc[0]) / total, 4)

    return rates
