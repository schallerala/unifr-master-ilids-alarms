import pandas as pd
from pydantic import BaseModel


class DataFrameDescription(BaseModel):
    description: str
    data_frame: pd.DataFrame

    @property
    def df(self) -> pd.DataFrame:
        return self.data_frame

    class Config:
        arbitrary_types_allowed = True
