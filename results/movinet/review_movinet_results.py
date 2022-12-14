import functools
import glob
import hashlib
import http
import io
import os
from email.utils import formatdate

import dash.development.base_component
import flask
import math
from dash.exceptions import PreventUpdate
from decord import VideoReader, cpu
from flask import Flask
from math import trunc
from typing import Tuple, Dict, List, Optional

from dash import Dash, html, dcc, Output, Input, State
import plotly.express as px
import pandas as pd
from itertools import permutations
from pathlib import Path
from PIL import Image

import numpy as np

from sklearn.metrics import (
    roc_curve,
    confusion_matrix,
    roc_auc_score,
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

N = 15
# 11 - logspace := this is to "reverse the logscale to have it on the end instead at the beginning of the scale"
# Or manually:
# cost_fn = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99, 0.999, 0.9999, 0.99999]

COST_FN = ((11 - np.logspace(0.000001, 1, N, endpoint=True)) / 10)[::-1]


ILIDS_PATH = SOURCE_PATH.parent.parent
assert ILIDS_PATH.exists() and ILIDS_PATH.is_dir()


def load_variation_df(movinet_variation):
    pickle_file = SOURCE_PATH / f"{movinet_variation}.pkl"
    features_df = pd.read_pickle(pickle_file)

    # features = features_df[FEATURES_COLUMNS_INDEXES].to_numpy()
    # features_df[FEATURES_COLUMNS_INDEXES] = (features / np.linalg.norm(features, axis=-1, keepdims=True)).tolist()

    df = SEQUENCES_DF.join(features_df)

    df["Clip"] = df.index
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


def get_conf_matrix_with_threshold(
    threshold: float, y_true: np.ndarray, df: pd.DataFrame
) -> np.ndarray:
    # Imagine setting the prediction threshold to the actual threshold
    y_pred = (df["Activation"] >= threshold).to_numpy(np.int32)

    TN, FP, FN, TP = confusion_matrix(y_true, y_pred).ravel()

    conf_matrix = np.array([[TP, FN], [FP, TN]])

    return conf_matrix


def get_cost_matrix(cost_ratio: float) -> np.ndarray:
    return np.array([[0, cost_ratio], [1 - cost_ratio, 0]])


def get_cost_function(cost_matrix, confusion_vector) -> np.ndarray:
    nb_thresholds = int(len(confusion_vector) / 4)

    tiled_cost_vector = np.tile(cost_matrix.ravel(), nb_thresholds)

    return (
        np.multiply(confusion_vector, tiled_cost_vector)
        .reshape((nb_thresholds, -1))
        .sum(axis=1)
    )


def get_confusion_vector(df, reversed_thresholds, y_true) -> np.ndarray:
    return np.array(
        [
            get_conf_matrix_with_threshold(threshold, y_true, df)
            for threshold in reversed_thresholds
        ]
    ).ravel()


def get_3d_cost_function(confusion_vector) -> np.ndarray:
    # Considering confusion matrix of the shape:
    # [[TP, FN],  X  [[C(TP) = 0,     C(FN) = X],   = Cost(T)
    #  [FP, TN]]      [C(FP) = 1 - X, c(TN) = 0]]

    z = np.array(
        [
            get_cost_function(get_cost_matrix(cost_ratio), confusion_vector)
            for cost_ratio in COST_FN
        ]
    )

    return z


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
ALL_ROC_CURVES_DF = {
    variation_name: pd.DataFrame(
        {
            "False Positive Rate": ALL_ROC_CURVES[variation_name][0],
            "True Positive Rate": ALL_ROC_CURVES[variation_name][1],
        },
        columns=pd.Index(["False Positive Rate", "True Positive Rate"], name="Rate"),
        index=pd.Index(ALL_ROC_CURVES[variation_name][2], name="Thresholds"),
    )
    for variation_name in VARIATION_NAMES
}
ALL_AUC_SCORES = {
    variation_name: roc_auc_score(*ALL_PREDICTIONS[variation_name])
    for variation_name in VARIATION_NAMES
}
ALL_CONFUSION_VECTOR_FOR_ALL_THRESHOLDS = {
    variation_name: get_confusion_vector(
        ALL_DF[variation_name],
        ALL_ROC_CURVES[variation_name][2][::-1],
        ALL_PREDICTIONS[variation_name][0],
    )
    for variation_name in VARIATION_NAMES
}
ALL_COST_FUNCTION_Z = {
    variation_name: get_3d_cost_function(
        ALL_CONFUSION_VECTOR_FOR_ALL_THRESHOLDS[variation_name],
    )
    for variation_name in VARIATION_NAMES
}

COST_LHS = 0.9
COST_RHS = 1.0 - COST_LHS


flask_app = Flask(__name__)


# Taken from: https://github.com/encode/starlette/blob/master/starlette/_compat.py
# ------------
# Compat wrapper to always include the `usedforsecurity=...` parameter,
# which is only added from Python 3.9 onwards.
# We use this flag to indicate that we use `md5` hashes only for non-security
# cases (our ETag checksums).
# If we don't indicate that we're using MD5 for non-security related reasons,
# then attempting to use this function will raise an error when used
# environments which enable a strict "FIPs mode".
#
# See issue: https://github.com/encode/starlette/issues/1365
try:

    # check if the Python version supports the parameter
    # using usedforsecurity=False to avoid an exception on FIPS systems
    # that reject usedforsecurity=True
    hashlib.md5(b"data", usedforsecurity=False)  # type: ignore[call-arg]

    def md5_hexdigest(
        data: bytes, *, usedforsecurity: bool = True
    ) -> str:  # pragma: no cover
        return hashlib.md5(  # type: ignore[call-arg]
            data, usedforsecurity=usedforsecurity
        ).hexdigest()

except TypeError:  # pragma: no cover

    def md5_hexdigest(data: bytes, *, usedforsecurity: bool = True) -> str:
        return hashlib.md5(data).hexdigest()


def get_image_path(image_name: str) -> Path:
    return ILIDS_PATH / "data" / "sequences" / image_name


@functools.cache
def get_image_array(name: str) -> np.ndarray:
    vr = VideoReader(str(get_image_path(name)), cpu(0))
    center_frame_idx = math.floor(len(vr) / 2)

    return vr[center_frame_idx].asnumpy()  # W, H, C


@functools.cache
def get_image_headers(image_name: str) -> Dict[str, str]:
    stat_result = os.stat(get_image_path(image_name))

    # content_length = str(stat_result.st_size)
    last_modified = formatdate(stat_result.st_mtime, usegmt=True)
    etag_base = str(stat_result.st_mtime) + "-" + str(stat_result.st_size)
    etag = md5_hexdigest(etag_base.encode(), usedforsecurity=False)

    return {
        # "content-length": content_length,
        "last-modified": last_modified,
        "etag": etag,
    }


@functools.cache
def get_cached_image_response(image_name: str) -> flask.Response:
    im = Image.fromarray(get_image_array(image_name))

    # save image to an in-memory bytes buffer
    with io.BytesIO() as buf:
        im.save(buf, format="PNG")
        im_bytes = buf.getvalue()

    headers = {
        "Content-Disposition": f'inline; filename="{image_name}"',
        **get_image_headers(image_name),
    }
    return flask.Response(im_bytes, headers=headers, mimetype="image/png")


@flask_app.route("/img/<image_name>")
def get_clip_middle_frame(image_name: str):
    if not (
        get_image_path(image_name).exists() and get_image_path(image_name).is_file()
    ):
        return flask.Response(status=http.HTTPStatus.NOT_FOUND)

    return get_cached_image_response(image_name)


app = Dash(server=flask_app, name=__name__)


expanded_rates_df = pd.concat(
    [get_rates_cost_df(movinet_variation) for movinet_variation in VARIATION_NAMES]
)


app.layout = html.Div(
    children=[
        html.H1("Without normalized features!"),
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
                # height=1000,
                height=500,
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
                histo_graph := dcc.Graph(id="histo-graph", style={"flex": 1}),
                rates_graph := dcc.Graph(id="rates-graph", style={"flex": 1}),
            ],
            style={"display": "flex"},
        ),
        html.Div(
            [
                roc_graph := dcc.Graph(id="roc-graph", style={"width": "600px"}),
                fn_preview_container := html.Div(
                    id="div-fn-preview", style={"flex": 1, "width": "100%"}
                ),
            ],
            style={"display": "flex"},
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
                cost_func_graph := dcc.Graph(id="cost-func-graph", style={"flex": "1"}),
                cost_func_confusion_matrix_graph := dcc.Graph(
                    id="cost-func-confusion-matrix-graph", style={"flex": "1"}
                ),
            ],
            style={"display": "flex"},
        ),
        html.Div(
            [
                contour_cost_func_graph := dcc.Graph(
                    id="contour-cost-func-graph", style={"flex": "1"}
                ),
                contour_cost_func_confusion_matrix_graph := dcc.Graph(
                    id="contour-cost-func-confusion-matrix-graph",
                    style={"flex": "1"},
                ),
            ],
            style={"display": "flex"},
        ),
    ]
)


@app.callback(Output(histo_graph, "figure"), Input(variation_items, "value"))
def get_histogram_by_thresholds(movinet_variation: str) -> go.Figure:
    return px.histogram(
        ALL_DF[movinet_variation],
        x="Activation",
        color="Alarm",
        marginal="rug",
        hover_name="Clip",
        nbins=50,
    )


@app.callback(Output(rates_graph, "figure"), Input(variation_items, "value"))
def get_true_false_rates(movinet_variation: str) -> go.Figure:
    return px.line(
        ALL_ROC_CURVES_DF[movinet_variation],
        title="TPR and FPR at every threshold",
        log_x=True,
    )


@app.callback(Output(roc_graph, "figure"), Input(variation_items, "value"))
def get_roc(movinet_variation: str) -> go.Figure:
    return px.line(
        ALL_ROC_CURVES_DF[movinet_variation],
        x="False Positive Rate",
        y="True Positive Rate",
        title=f"{movinet_variation} - AUC: {ALL_AUC_SCORES[movinet_variation]:.3f}",
        color_discrete_sequence=["orange"],
        range_x=[0, 1],
        range_y=[0, 1],
        width=600,
        height=450,
    ).add_shape(type="line", line=dict(dash="dash"), x0=0, x1=1, y0=0, y1=1)


@app.callback(
    Output(fn_preview_container, "children"),
    Input(roc_graph, "hoverData"),
    State(variation_items, "value"),
)
def preview_fn_on_roc_hover(
    hoverData: Optional[Dict], variation_name: str
) -> List[dash.development.base_component.Component]:
    if not hoverData:
        raise PreventUpdate

    point = hoverData["points"][0]
    # corresponds to the threshold index
    point_idx = point["pointIndex"]

    # get all TN from -Inf to threshold[idx]
    threshold = ALL_ROC_CURVES[variation_name][2][point_idx]

    FN_df = ALL_DF[variation_name][
        (threshold > ALL_DF[variation_name]["Activation"])
        & ALL_DF[variation_name]["Alarm"]
    ]

    def _get_fn_div(clip_name: str) -> html.Div:
        return html.Div(
            [
                html.Div([html.Img(src=f"/img/{clip_name}", style={"width": "180px"})]),
                html.Div([html.Span(f"{clip_name}")]),
            ]
        )

    return [
        html.H4(
            f"FN clips at this rate: {len(FN_df)}/{len(ALL_DF[variation_name])} with threshold: {threshold:.2f} on {variation_name}"
        ),
        html.Div(
            [
                _get_fn_div(index.lstrip("data/sequences/"))
                for index, row_s in list(FN_df.sort_values("Activation").iterrows())[
                    :80
                ]
            ],
            style={
                "width": "100%",
                "display": "grid",
                "gridTemplateColumns": "repeat(4, auto)",
                "gap": "4px",
            },
        ),
    ]


@app.callback(
    Output(cost_func_graph, "figure"),
    Input(variation_items, "value"),
    Input(cost_function_ratio_slider, "value"),
)
def get_elementwise_cost_function(
    movinet_variation: str, cost_ratio_idx: int
) -> go.Figure:
    reversed_thresholds = ALL_ROC_CURVES[movinet_variation][2][::-1]

    fig = go.Figure()

    cost_ratio = COST_FN[cost_ratio_idx]

    cost_function_y = ALL_COST_FUNCTION_Z[movinet_variation][cost_ratio_idx]
    fig.add_trace(
        go.Scatter(
            x=reversed_thresholds,
            y=cost_function_y,
            name="Cost(T)",
            mode="lines+markers",
            marker=go.scatter.Marker(size=5),
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
                symbol="x-thin",
                line=go.scatter.marker.Line(width=4, color="orange"),
                size=14,
                color="orange",
            ),
        )
    )

    fig.update_layout(
        title_text=f"Cost(T), with Cost(FN) = {trunc(cost_ratio * 1000) / 1000:.3f} of {movinet_variation}"
    )

    fig.update_xaxes(type="log")

    return fig


@app.callback(
    Output(contour_cost_func_graph, "figure"),
    Input(variation_items, "value"),
)
def get_elementwise_3d_cost_function(movinet_variation: str) -> go.Figure:
    reversed_thresholds = ALL_ROC_CURVES[movinet_variation][2][::-1]

    fig = go.Figure()

    z = ALL_COST_FUNCTION_Z[movinet_variation]

    y_vals = list(range(len(COST_FN)))
    fig.add_trace(
        go.Contour(
            x=reversed_thresholds,
            y=y_vals,
            z=z,
            name="Cost(T)",
        )
    )

    mins_x_idx = z.argmin(axis=1)
    min_costs = np.take_along_axis(z, np.expand_dims(mins_x_idx, axis=1), axis=1)

    fig.add_trace(
        go.Scatter(
            x=reversed_thresholds[mins_x_idx],
            y=y_vals,
            customdata=min_costs,
            name="Min for FN factor",
            texttemplate="%{customdata[0]:.2f}",
            textposition="middle right",
            textfont=dict(color="white"),
            marker=go.scatter.Marker(
                symbol="x-thin",
                line=go.scatter.marker.Line(width=2, color="white"),
                size=7,
                color="white",
            ),
            mode="lines+markers+text",
        )
    )

    fig.update_layout(title_text=f"Cost(T) of {movinet_variation}")

    fig.update_xaxes(
        range=[np.log10(reversed_thresholds[0]), np.log10(reversed_thresholds[-1])],
        type="log",
    )
    fig.update_yaxes(
        range=[y_vals[0], y_vals[-1]],
        tickmode="array",
        tickvals=y_vals,
        ticktext=[f"{trunc(cost_ratio * 1000) / 1000:.3f}" for cost_ratio in COST_FN],
    )

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

    point = hoverData["points"][0]
    cost = point["y"]
    threshold = point["x"]

    df = ALL_DF[movinet_variation]
    y_true = ALL_PREDICTIONS[movinet_variation][0]

    confusion_matrix_population = get_conf_matrix_with_threshold(threshold, y_true, df)
    TP, FN, FP, TN = confusion_matrix_population.ravel()

    Z = [[FP, TN], [TP, FN]]

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
        title_text=f"Confusion Matrix (Cost(T = {trunc(threshold * 1000) / 1000}) = {trunc(cost * 1000) / 1000:.3f} of {movinet_variation})"
    )

    # adjust margins to make room for y, x axis title
    fig.update_layout(margin=dict(t=90, l=120))

    # add colorbar
    fig["data"][0]["showscale"] = True

    return fig


@app.callback(
    Output(contour_cost_func_confusion_matrix_graph, "figure"),
    Input(variation_items, "value"),
    Input(contour_cost_func_graph, "hoverData"),
)
def display_cost_function_confusion_matrix_from_contour(
    movinet_variation: str, hoverData: Dict
) -> go.Figure:
    fig = go.Figure()

    if not (movinet_variation and hoverData):
        return fig

    point = hoverData["points"][0]
    threshold = point["x"]
    cost = point["z"] if "z" in point else point["customdata"][0]

    df = ALL_DF[movinet_variation]
    y_true = ALL_PREDICTIONS[movinet_variation][0]

    confusion_matrix_population = get_conf_matrix_with_threshold(threshold, y_true, df)
    TP, FN, FP, TN = confusion_matrix_population.ravel()

    Z = [[FP, TN], [TP, FN]]

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
        title_text=f"Confusion Matrix (Cost(T = {trunc(threshold * 1000) / 1000}) = {trunc(cost * 1000) / 1000:.3f} of {movinet_variation})"
    )

    # adjust margins to make room for y, x axis title
    fig.update_layout(margin=dict(t=90, l=120))

    # add colorbar
    fig["data"][0]["showscale"] = True

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
