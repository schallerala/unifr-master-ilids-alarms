import pandas as pd
import torch
import towhee
import tqdm

import ilids.towhee_utils.log_progress_operator
from ilids.towhee_utils.override.movinet import Movinet, MovinetModelName


def extract_movinet_features(
    model_name: MovinetModelName,
    input_glob_pattern: str,
) -> pd.DataFrame:
    assert model_name.value in Movinet.supported_model_names()

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

    return df
