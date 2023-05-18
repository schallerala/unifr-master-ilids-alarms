import glob
import os
from math import trunc
from pathlib import Path
from typing import Dict, List, Tuple

import dash
import numpy as np
import open_clip
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import torch
from dash import Dash, Input, Output, State, dash_table, dcc, html

from ilids.models.actionclip.factory import create_models_and_transforms

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


model_text = create_models_and_transforms(
    actionclip_pretrained_ckpt=SOURCE_PATH.parent.parent
    / "ckpt"
    / "actionclip"
    / "vit-b-16-8f.pt",
    openai_model_name="ViT-B-16",
    extracted_frames=8,
    device=torch.device("cpu"),
)[1]


app.layout = html.Div(
    children=[
        texts_local_store := dcc.Store(id="texts-local-store", storage_type="local"),
        new_text_input := dcc.Input(
            id="new-text-input", type="search", value="", debounce=True
        ),
        submit_new_text_input := html.Button("Add", id="submit-new-text-btn"),
        input_text_data_table := dash_table.DataTable(
            id="input-text-data-table",
            data=[],
            columns=[
                {"name": col, "id": col} for col in ["index", "text", "spark-features"]
            ],
            row_deletable=True,
            persistence=True,
            persisted_props=["data"],
            persistence_type="local",
            style_data_conditional=[
                {
                    "if": {"column_id": "spark-features"},
                    "font-family": "Sparks-Bar-Narrow",
                }
            ],
        ),
    ]
)


def get_text_features(text: str) -> np.ndarray:
    tokenized_text = open_clip.tokenize([text])

    with torch.no_grad():
        return model_text(tokenized_text).numpy().ravel()


def get_sparklines(features: np.ndarray) -> str:
    f_min = features.min(initial=None)
    f_max = features.max(initial=None)

    sparkline = (
        ((features - f_min) * (1 / (f_max - f_min)) * 100).astype(np.int32).tolist()
    )

    joined_sparkline = f"{{{','.join(list(map(lambda x: str(x), sparkline)))}}}"
    return joined_sparkline


@dash.callback(
    [Output(input_text_data_table, "data"), Output(new_text_input, "value")],
    [
        Input(submit_new_text_input, "n_clicks"),
        Input(new_text_input, "value"),
        Input(input_text_data_table, "data"),
        # Since we use the data prop in an output,
        # we cannot get the initial data on load with the data prop.
        # To counter this, you can use the modified_timestamp
        # as Input and the data as State.
        # This limitation is due to the initial None callbacks
        # https://github.com/plotly/dash-renderer/pull/81
        Input(texts_local_store, "modified_timestamp"),
    ],
    [State(texts_local_store, "data")],
)
def update_texts_dataframe(
    submit: int,
    new_text: str,
    current_text_data: List[Dict],
    ts,
    local_storage_text_data: List[Dict],
) -> Tuple[List[Dict], str]:

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    current_text_data = (
        local_storage_text_data
        if trigger_id == texts_local_store.id
        else current_text_data
    )

    new_entry_df = (
        pd.DataFrame(
            [dict(text=new_text, features=get_sparklines(get_text_features(new_text)))]
        )
        if new_text
        else pd.DataFrame()
    )

    if len(current_text_data) > 0:
        df = pd.concat(
            (
                pd.DataFrame.from_records(current_text_data).set_index("index"),
                new_entry_df,
            ),
            ignore_index=True,
        )
        # need to recompute features
        if trigger_id == texts_local_store.id:
            df["spark-features"] = pd.Series(
                [
                    get_sparklines(get_text_features(text))
                    for index, text in df["text"].items()
                ]
            )
    else:
        df = new_entry_df

    df = df.drop_duplicates("text")

    return df.reset_index().to_dict("records"), ""


@app.callback(Output(texts_local_store, "data"), Input(input_text_data_table, "data"))
def persist_text_data_table(current_text_data: List[Dict]) -> List[Dict]:
    if len(current_text_data) == 0:
        return []

    df = pd.DataFrame.from_records(current_text_data).set_index("index")

    return df[["text"]].reset_index().to_dict("records")


if __name__ == "__main__":
    app.run_server(debug=True)
