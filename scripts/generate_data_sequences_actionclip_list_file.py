from pathlib import Path
from time import strftime, gmtime
from typing import Optional

import numpy as np
import pandas as pd
import typer


def main(
    tp_fp_sequences_file: Path,
    output: Path,
    initial_fps: int,
    extracted_sequences_folder: Path,
    extracted_frame_stride: int,
    new_fps: Optional[int] = typer.Option(None),
    overwrite: bool = typer.Option(False, "--force", "-f"),
):
    assert tp_fp_sequences_file.exists()
    assert tp_fp_sequences_file.is_file()

    assert output.parent.exists()
    assert overwrite or not output.exists()

    if not new_fps:
        new_fps = initial_fps

    df = pd.read_csv(tp_fp_sequences_file, index_col=0)

    df["Duration"] = pd.to_timedelta(df["Duration"])

    # To compute the number of frames: math.ceil((initial_duration * fps) / extracted_frames + 1)
    file_paths = str(extracted_sequences_folder).rstrip("/") + "/" + df.index
    frames_count = (
        df["Duration"].dt.seconds * initial_fps / extracted_frame_stride + 1
    ).apply(np.ceil).astype('int64')
    # To have its time in seconds, same formula as above but lastly divided by the new fps (here same)
    new_duration = (frames_count / new_fps).apply(
        lambda secs: strftime("%H:%M:%S", gmtime(secs))
    )

    new_df = pd.DataFrame(
        np.array([file_paths, frames_count, new_duration]).T,
        columns=["sequence", "frame_count", "duration"],
    ).set_index("sequence")

    new_df.to_csv(output)


if __name__ == "__main__":
    typer.run(main)
