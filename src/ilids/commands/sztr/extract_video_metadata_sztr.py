from pathlib import Path

import typer

from ilids.preprocessing.common import ffprobe_videos, ffprobe_videos_to_df
from ilids.preprocessing.sztr.video_folder import VIDEOS_CSV_FIELDS_DESCRIPTION

typer_app = typer.Typer()

"""Commands structure:

    sztr-videos
       ├── ffprobe      # print out ffprobe results
       └── meta         # print out file's description
"""


@typer_app.command()
def ffprobe(video_folder: Path, video_extension: str = ".mov"):
    assert (
        video_folder.exists() and video_folder.is_dir()
    ), "Expecting video folder as first argument"

    df = ffprobe_videos_to_df(ffprobe_videos(video_folder, video_extension))
    df = df.set_index("format.filename")

    print(df.to_csv())


@typer_app.command()
def meta():
    print(VIDEOS_CSV_FIELDS_DESCRIPTION)
