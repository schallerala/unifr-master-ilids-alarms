from pathlib import Path

import pandas as pd
import torch
import towhee
import tqdm

import ilids.towhee_utils.log_progress_operator
from ilids.towhee_utils.override.movinet import Movinet, MovinetModelName
from ilids.utils.persistence_method import PandasPersistenceMethod, PersistenceMethod


def extract_movinet_features(
    model_name: MovinetModelName,
    input_glob_pattern: str,
    features_output: Path,
    persist_method: PersistenceMethod,
):
    assert model_name.value in Movinet.supported_model_names()
    assert issubclass(type(persist_method), PandasPersistenceMethod), type(
        persist_method
    )

    all_sequences = towhee.glob["path"](input_glob_pattern)

    progress = tqdm.tqdm(
        f"Features extraction with {model_name}", total=len(all_sequences.to_list())
    )

    with torch.no_grad():
        movinet_entites = (
            all_sequences.video_decode.ffmpeg["path", "frames"]()
            .stream()
            .ilids.movinet["frames", ("labels", "scores", "features")](
                model_name=model_name.value
            )
            .select["path", "features"]()
            .ilids.log_progress(progress)
            .unstream()
            .to_list()
        )

    df = pd.DataFrame(
        [[entity.path, *entity.features] for entity in movinet_entites],
        columns=(["path"] + list(range(600))),
    ).set_index("path")

    persist_method.persist(features_output, df)
