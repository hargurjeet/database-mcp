import duckdb
import pandas as pd
from .base import BaseConnector


class DuckDBConnector(BaseConnector):

    def __init__(self, config: dict):
        self.conn = duckdb.connect(config["db_path"])

    def execute(self, query: str) -> pd.DataFrame:
        return self.conn.execute(query).fetchdf()

    def list_tables(self) -> list[str]:
        rows = self.conn.execute("SHOW TABLES").fetchall()
        return [r[0] for r in rows]

    def get_schema(self, table: str) -> list[dict]:
        rows = self.conn.execute(f"DESCRIBE {table}").fetchall()
        return [{"column": r[0], "type": r[1]} for r in rows]

    def close(self):
        self.conn.close()
