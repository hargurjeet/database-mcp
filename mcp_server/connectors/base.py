from abc import ABC, abstractmethod
import pandas as pd


class BaseConnector(ABC):

    @abstractmethod
    def execute(self, query: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_schema(self, table: str) -> list[dict]:
        pass

    @abstractmethod
    def close(self):
        pass
