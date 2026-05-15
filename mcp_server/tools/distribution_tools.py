from mcp_server.connectors.base import BaseConnector


def get_distribution_stats(connector: BaseConnector, table: str, column: str) -> dict:
    df = connector.execute(f"""
        SELECT
            AVG({column})    AS mean,
            STDDEV({column}) AS std,
            MIN({column})    AS min,
            MAX({column})    AS max,
            COUNT({column})  AS count
        FROM {table}
    """)
    row = df.iloc[0]

    def _f(val):
        return float(val) if val is not None else None

    return {
        "column": column,
        "mean": _f(row["mean"]),
        "std": _f(row["std"]),
        "min": _f(row["min"]),
        "max": _f(row["max"]),
        "count": int(row["count"]),
        "z_score_threshold": 3.0,
    }
