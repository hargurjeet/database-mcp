from mcp_server.connectors.base import BaseConnector


def detect_timestamp_gaps(connector: BaseConnector, table: str, column: str) -> dict:
    stats_df = connector.execute(f"""
        SELECT
            MIN({column}) AS min_ts,
            MAX({column}) AS max_ts,
            COUNT({column}) AS row_count
        FROM {table}
    """)
    row = stats_df.iloc[0]
    row_count = int(row["row_count"])

    if row_count < 2:
        return {
            "column": column,
            "row_count": row_count,
            "large_gaps_detected": False,
            "detail": "Not enough rows to detect gaps",
        }

    gaps_df = connector.execute(f"""
        SELECT
            datediff('second',
                LAG({column}) OVER (ORDER BY {column}),
                {column}
            ) AS gap_seconds
        FROM {table}
        WHERE {column} IS NOT NULL
    """)
    gaps_df = gaps_df.dropna(subset=["gap_seconds"])

    if gaps_df.empty:
        return {"column": column, "row_count": row_count, "large_gaps_detected": False}

    median_gap = float(gaps_df["gap_seconds"].median())
    max_gap = float(gaps_df["gap_seconds"].max())
    threshold = median_gap * 10 if median_gap > 0 else 1
    large_gaps = gaps_df[gaps_df["gap_seconds"] > threshold]

    return {
        "column": column,
        "row_count": row_count,
        "min_ts": str(row["min_ts"]),
        "max_ts": str(row["max_ts"]),
        "median_gap_seconds": round(median_gap, 2),
        "max_gap_seconds": round(max_gap, 2),
        "large_gaps_detected": bool(len(large_gaps) > 0),
        "large_gap_count": int(len(large_gaps)),
    }
