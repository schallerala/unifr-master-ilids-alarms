import glob
import os
from math import trunc
from typing import Dict, List, Tuple

import dash
from dash import Dash, html, dcc, Output, Input, dash_table
import plotly.express as px
import pandas as pd
from pathlib import Path

import numpy as np

import plotly.graph_objects as go

SOURCE_PATH = Path(os.path.dirname(os.path.abspath(__file__)))

FEATURES_COLUMNS_INDEXES = pd.RangeIndex.from_range(range(512))

VARIATION_PATHS = list(
    map(lambda result_file: Path(result_file), glob.glob(str(SOURCE_PATH / "*.pkl")))
)
VARIATION_NAMES = sorted(
    list(map(lambda result_path: result_path.stem, VARIATION_PATHS))
)

tp_fp_sequences_path = (
    SOURCE_PATH.parent.parent / "data" / "handcrafted-metadata" / "tp_fp_sequences.csv"
)
SEQUENCES_DF = pd.read_csv(tp_fp_sequences_path, index_col=0)
# Only keep relevant columns
SEQUENCES_DF = SEQUENCES_DF[
    [
        "Classification",
        "Duration",
        "Distance",
        "SubjectApproachType",
        "SubjectDescription",
        "Distraction",
        "Stage",
    ]
]
# Fix index prefix for join
SEQUENCES_DF = SEQUENCES_DF.set_index("data/sequences/" + SEQUENCES_DF.index)


def load_variation_df(movinet_variation):
    pickle_file = SOURCE_PATH / f"{movinet_variation}.pkl"
    features_df = pd.read_pickle(pickle_file)

    df = SEQUENCES_DF.join(features_df)

    df["Alarm"] = df["Classification"] == "TP"
    # For each sample, get the highest feature/signal
    df["Activation"] = df[FEATURES_COLUMNS_INDEXES].max(axis=1)

    return df


ALL_DF = {
    variation_name: load_variation_df(variation_name)
    for variation_name in VARIATION_NAMES
}

app = Dash(__name__)


app.layout = html.Div(
    children=[
        new_text_input := dcc.Input(id="new-text-input", type="search", debounce=True),
        submit_new_text_input := html.Button("Add", id="submit-new-text-btn"),
        input_text_data_table := dash_table.DataTable(
            id="input-text-data-table",
            data=[],
            columns=[{"name": col, "id": col} for col in ["index", "text"]],
            row_deletable=True,
        ),
    ]
)


@dash.callback(
    [Output(input_text_data_table, "data"), Output(new_text_input, "value")],
    [
        Input(submit_new_text_input, "n_clicks"),
        Input(new_text_input, "value"),
        Input(input_text_data_table, "data"),
    ],
)
def add_text(
    submit: int, new_text: str, current_text_data: List[Dict]
) -> Tuple[List[Dict], str]:
    new_entry_df = pd.DataFrame([dict(text=new_text)]) if new_text else pd.DataFrame()

    if len(current_text_data) > 0:
        df = pd.concat(
            (
                pd.DataFrame.from_records(current_text_data).set_index("index"),
                new_entry_df,
            ),
            ignore_index=True,
        )
    else:
        df = new_entry_df

    df = df.drop_duplicates("text")

    return df.reset_index().to_dict("records"), ""


if __name__ == "__main__":
    app.run_server(debug=True)
