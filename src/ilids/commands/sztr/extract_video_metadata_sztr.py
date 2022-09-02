from pathlib import Path

import pandas as pd
import typer

from ilids.preprocessing.common import ffprobe_videos
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

    ffprobes = ffprobe_videos(video_folder, video_extension)

    df = pd.json_normalize([ffprobe.dict() for ffprobe in ffprobes])

    print(df.to_csv())


@typer_app.command()
def meta():
    print(VIDEOS_CSV_FIELDS_DESCRIPTION)


if __name__ == "__main__":
    typer_app()
