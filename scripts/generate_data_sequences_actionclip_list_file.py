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
    frame_stride: int,
    new_fps: Optional[int] = typer.Option(None),
    overwrite: bool = typer.Option(False, "--force", "-f"),
):
    assert tp_fp_sequences_file.exists()
    assert tp_fp_sequences_file.is_file()

    assert output.parent.exists()
    # assert overwrite or not output.exists()

    if not new_fps:
        new_fps = initial_fps

    df = pd.read_csv(tp_fp_sequences_file, index_col=0)

    df["Duration"] = pd.to_timedelta(df["Duration"])

    # To compute the number of frames:
    #   if (initial_duration * fps - 1) % frame_stride == 0:
    #       math.ceil((initial_duration * fps) / frame_stride)
    #   else:
    #       math.ceil((initial_duration * fps) / frame_stride + 1)
    file_paths = str(extracted_sequences_folder).rstrip("/") + "/" + df.index
    total_frames = df["Duration"].dt.seconds * initial_fps
    nb_frames = total_frames / frame_stride

    missing_last_frame = (total_frames - 1) % frame_stride > 0

    nb_frames[missing_last_frame] += 1

    nb_frames = nb_frames.apply(np.ceil).astype('int64')
    # To have its time in seconds, same formula as above but lastly divided by the new fps (here same)
    new_duration = (nb_frames / new_fps).apply(
        lambda secs: strftime("%H:%M:%S", gmtime(secs))
    )

    new_df = pd.DataFrame(
        np.array([file_paths, nb_frames, new_duration]).T,
        columns=["sequence", "frame_count", "duration"],
    ).set_index("sequence")

    new_df.to_csv(output)


if __name__ == "__main__":
    typer.run(main)
