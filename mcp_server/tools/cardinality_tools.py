from mcp_server.connectors.base import BaseConnector


def get_cardinality(connector: BaseConnector, table: str, column: str) -> dict:
    distinct_df = connector.execute(
        f"SELECT COUNT(DISTINCT {column}) AS distinct_count FROM {table}"
    )
    distinct_count = int(distinct_df["distinct_count"].iloc[0])

    top_df = connector.execute(f"""
        SELECT {column} AS value, COUNT(*) AS freq
        FROM {table}
        WHERE {column} IS NOT NULL
        GROUP BY {column}
        ORDER BY freq DESC
        LIMIT 10
    """)

    return {
        "column": column,
        "distinct_count": distinct_count,
        "top_values": top_df.to_dict(orient="records"),
    }
