from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd


class PersistenceMethod(ABC):
    @abstractmethod
    def persist(self, path: Path, obj: Any):
        raise NotImplementedError()


class PandasPersistenceMethod(PersistenceMethod, ABC):
    @abstractmethod
    def persist(self, path: Path, df: pd.DataFrame):
        ...


class CsvPandasPersistenceMethod(PandasPersistenceMethod):
    def persist(self, path: Path, df: pd.DataFrame):
        df.to_csv(path)


class PicklePandasPersistenceMethod(PandasPersistenceMethod):
    def persist(self, path: Path, df: pd.DataFrame):
        df.to_pickle(str(path))
