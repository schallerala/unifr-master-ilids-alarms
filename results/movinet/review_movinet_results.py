import glob
import os
from math import trunc
from typing import Tuple, Dict

from dash import Dash, html, dcc, Output, Input
import plotly.express as px
import pandas as pd
from itertools import permutations
from pathlib import Path

import numpy as np

from sklearn.metrics import (
    roc_curve,
    confusion_matrix,
)

import plotly.graph_objects as go

SOURCE_PATH = Path(os.path.dirname(os.path.abspath(__file__)))

FEATURES_COLUMNS_INDEXES = pd.RangeIndex.from_range(range(600))

RATES_PERMUTATIONS = list(permutations(["tpr", "fpr", "fnr", "tnr"], r=2))

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


def get_predictions(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    y_true = df["Alarm"].to_numpy(dtype=np.int32)
    y_scores = df["Activation"].to_numpy()

    return y_true, y_scores


def get_rates_cost_df(movinet_variation: str) -> pd.DataFrame:
    fpr, tpr, thresholds = ALL_ROC_CURVES[movinet_variation]

    rates = dict(tpr=tpr, fpr=fpr, fnr=(1 - tpr), tnr=(1 - fpr))

    rates_df = pd.DataFrame(
        [
            [rate1, rate2, *(COST_LHS * rates[rate1] + COST_RHS * rates[rate2])]
            for rate1, rate2 in RATES_PERMUTATIONS
        ],
        columns=(["rate1", "rate2"] + list(range(len(thresholds)))),
    ).set_index(["rate1", "rate2"])

    expanded_rates_df = (
        pd.melt(
            rates_df.reset_index(),
            id_vars=["rate1", "rate2"],
            value_vars=pd.RangeIndex(len(thresholds)),
            var_name="x",
            value_name="y",
        )
        .sort_values(by=["rate1", "rate2", "x", "y"])
        .reset_index()
    )

    expanded_rates_df["variation"] = movinet_variation

    return expanded_rates_df


ALL_DF = {
    variation_name: load_variation_df(variation_name)
    for variation_name in VARIATION_NAMES
}
ALL_PREDICTIONS = {
    variation_name: get_predictions(ALL_DF[variation_name])
    for variation_name in VARIATION_NAMES
}
ALL_ROC_CURVES = {
    variation_name: roc_curve(*ALL_PREDICTIONS[variation_name])
    for variation_name in VARIATION_NAMES
}

COST_LHS = 0.9
COST_RHS = 1.0 - COST_LHS

app = Dash(__name__)

expanded_rates_df = pd.concat(
    [get_rates_cost_df(movinet_variation) for movinet_variation in VARIATION_NAMES]
)


def get_conf_matrix_with_threshold(
    threshold: float, y_true: np.ndarray, df: pd.DataFrame
) -> np.ndarray:
    # Imagine setting the prediction threshold to the actual threshold
    y_pred = (df["Activation"] >= threshold).to_numpy(np.int32)

    TN, FP, FN, TP = confusion_matrix(y_true, y_pred).ravel()

    conf_matrix = np.array([[TP, FN], [FP, TN]])

    return conf_matrix


def confusion_matrix_to_str(confusion_matrix: np.ndarray) -> str:
    TP, FN, FP, TN = confusion_matrix.ravel()
    return f"TP={TP}, FN={FN}, FP={FP}, TN={TN}"


N = 15
# 11 - logspace := this is to "reverse the logscale to have it on the end instead at the beginning of the scale"
COST_FN = ((11 - np.logspace(0.000001, 1, N, endpoint=True)) / 10)[::-1]
# Or manually:
# cost_fn = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99, 0.999, 0.9999, 0.99999]


app.layout = html.Div(
    children=[
        grid_facet_rate_costs_graph := dcc.Graph(
            id="grid-facet-rate-costs-graph",
            figure=px.line(
                expanded_rates_df,
                x="x",
                y="y",
                facet_row="rate1",
                facet_col="rate2",
                color="variation",
                log_x=True,
                category_orders={
                    "rate1": ["tpr", "fnr", "fpr", "tnr"],
                    "rate2": ["tpr", "fnr", "fpr", "tnr"],
                },
                height=1000,
                # height=60,
            ),
        ),
        variation_items := dcc.RadioItems(
            id="variation-items",
            options=VARIATION_NAMES,
            value=VARIATION_NAMES[0],
            inline=True,
        ),
        html.Div(
            [
                cost_function_ratio_slider := dcc.Slider(
                    min=0,
                    max=len(COST_FN) - 1,
                    step=None,
                    id="cost-function-ratio-slider",
                    vertical=True,
                    marks={
                        i: str(trunc(cost_ratio * 1000) / 1000)
                        for i, cost_ratio in enumerate(COST_FN)
                    },
                    value=len(COST_FN) - 1,
                ),
                cost_func_graph := dcc.Graph(
                    id="cost-func-graph", style={"gridColumn": "2 / span 3"}
                ),
                cost_func_confusion_matrix_graph := dcc.Graph(
                    id="cost-func-confusion-matrix-graph",
                    style={"gridColumn": "5 / span 2"},
                ),
            ],
            style={"display": "grid", "gridTemplateColumns": "66px repeat(6, auto)"},
        ),
    ]
)


@app.callback(
    Output(cost_func_graph, "figure"),
    Input(variation_items, "value"),
    Input(cost_function_ratio_slider, "value"),
)
def get_elementwise_cost_function(
    movinet_variation: str, cost_ratio_idx: int
) -> go.Figure:
    df = ALL_DF[movinet_variation]
    reversed_thresholds = ALL_ROC_CURVES[movinet_variation][2][::-1]
    y_true = ALL_PREDICTIONS[movinet_variation][0]

    fig = go.Figure()

    # Considering confusion matrix of the shape:
    # [[TP, FN],  X  [[C(TP) = 0,     C(FN) = X],   = Cost(T)
    #  [FP, TN]]      [C(FP) = 1 - X, c(TN) = 0]]

    cost_ratio = COST_FN[cost_ratio_idx]
    cost_matrix = np.array([[0, cost_ratio], [1 - cost_ratio, 0]])


    cost_function_y = np.array(
        [
            np.multiply(
                get_conf_matrix_with_threshold(threshold, y_true, df), cost_matrix
            ).sum()
            for threshold in reversed_thresholds
        ]
    )

    fig.add_trace(
        go.Scatter(
            x=reversed_thresholds,
            y=cost_function_y,
            name="Cost(T)"
        )
    )

    y_min = cost_function_y.min(initial=None)
    min_arg = np.where(cost_function_y == y_min)

    # Markers: https://plotly.com/python/marker-style/
    fig.add_trace(
        go.Scatter(
            x=reversed_thresholds[min_arg],
            y=[y_min] * len(min_arg),
            name="Minimum",
            text=f"Min Cost(T) = {y_min:.3f}",
            marker=go.scatter.Marker(
                symbol="line-ns",
                line=go.scatter.marker.Line(width=4, color="orange"),
                size=25,
                color="orange",
            ),
        )
    )

    fig.update_layout(title_text=f"Cost(T) of {movinet_variation}")

    fig.update_xaxes(type="log")

    # adjust margins to make room for y, x axis title
    fig.update_layout(margin=dict(t=90, l=120))

    return fig


@app.callback(
    Output(cost_func_confusion_matrix_graph, "figure"),
    Input(variation_items, "value"),
    Input(cost_func_graph, "hoverData"),
)
def display_cost_function_confusion_matrix(
    movinet_variation: str, hoverData: Dict
) -> go.Figure:
    fig = go.Figure()

    if not (movinet_variation and hoverData):
        return fig

    threshold = hoverData["points"][0]["x"]

    df = ALL_DF[movinet_variation]
    y_true = ALL_PREDICTIONS[movinet_variation][0]

    confusion_matrix_population = get_conf_matrix_with_threshold(threshold, y_true, df)
    TN, FP, FN, TP = confusion_matrix_population.ravel()

    Z = [[TN, FP], [FN, TP]]

    X_LABELS = ["Positive (Alarm)", "Negative"]
    Y_LABELS = ["Negative", "Positive (Alarm)"]

    fig.add_trace(
        go.Heatmap(
            z=Z,
            x=X_LABELS,
            y=Y_LABELS,
            texttemplate="%{z}",
            colorscale="Viridis",
        )
    )

    # add custom xaxis title
    fig.add_annotation(
        dict(
            font=dict(color="black", size=14),
            x=0.5,
            y=1.1,
            showarrow=False,
            text="Predicted value",
            xref="paper",
            yref="paper",
        )
    )

    # add custom yaxis title
    fig.add_annotation(
        dict(
            font=dict(color="black", size=14),
            x=-0.05,
            y=0.5,
            showarrow=False,
            text="Real value",
            textangle=-90,
            xref="paper",
            yref="paper",
        )
    )

    fig.update_layout(
        title_text=f"Confusion Matrix (threshold: {trunc(threshold * 1000) / 1000} of {movinet_variation})"
    )

    # adjust margins to make room for y, x axis title
    fig.update_layout(margin=dict(t=90, l=120))

    # add colorbar
    fig["data"][0]["showscale"] = True

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
