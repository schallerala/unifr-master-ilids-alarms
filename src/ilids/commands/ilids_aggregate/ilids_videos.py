from pathlib import Path

import pandas as pd
import typer

from ilids.preprocessing.common import ffprobe_videos, ffprobe_videos_to_df
from ilids.preprocessing.sztr.video_folder import VIDEOS_CSV_FIELDS_DESCRIPTION

typer_app = typer.Typer()

"""Commands structure:

    ilids-videos
       ├── ffprobe      # print out ffprobe results
       └── meta         # print out file's description

Will merge the result of the sub-commands 'szte-videos' and 'sztr-videos'
"""


@typer_app.command()
def ffprobe(
    szte_video_folder: Path, sztr_video_folder: Path, video_extension: str = ".mov"
):
    assert (
        szte_video_folder.exists() and szte_video_folder.is_dir()
    ), "Expecting SZTE video folder as first argument"
    assert (
        sztr_video_folder.exists() and sztr_video_folder.is_dir()
    ), "Expecting SZTR video folder as first argument"

    szte_ffprobes_df = ffprobe_videos_to_df(
        ffprobe_videos(szte_video_folder, video_extension)
    )
    szte_ffprobes_df["format.filename"] = (
        "SZTE/video/" + szte_ffprobes_df["format.filename"]
    )
    sztr_ffprobes_df = ffprobe_videos_to_df(
        ffprobe_videos(sztr_video_folder, video_extension)
    )
    sztr_ffprobes_df["format.filename"] = (
        "SZTR/video/" + sztr_ffprobes_df["format.filename"]
    )

    df = pd.concat([szte_ffprobes_df, sztr_ffprobes_df])
    df = df.set_index("format.filename")

    print(df.to_csv())


@typer_app.command()
def meta():
    print(VIDEOS_CSV_FIELDS_DESCRIPTION)
