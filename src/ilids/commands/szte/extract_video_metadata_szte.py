from pathlib import Path

import typer

from ilids.preprocessing.common import ffprobe_videos, ffprobe_videos_to_df
from ilids.preprocessing.szte.video_folder import (
    VIDEOS_CSV_FIELDS_DESCRIPTION,
    extract_clean_videos_from_xml_files,
    merge_xml_video_and_ffprobes_dfs,
)

typer_app = typer.Typer()

"""Commands structure:

    szte-videos
       ├── merged       # print out merged ilids video's metadata and ffprobe results
       ├── original     # print out ilids (relevant) video's metadata
       ├── ffprobe      # print out ffprobe results
       └── meta         # print out file's description
"""


@typer_app.command()
def merged(video_folder: Path, video_extension: str = ".mov"):
    assert (
        video_folder.exists() and video_folder.is_dir()
    ), "Expecting video folder as first argument"

    ilids_video_xml_df = extract_clean_videos_from_xml_files(video_folder)
    ffprobes_df = ffprobe_videos_to_df(ffprobe_videos(video_folder, video_extension))

    df = merge_xml_video_and_ffprobes_dfs(
        ilids_video_xml_df, ffprobes_df, video_extension
    )
    df = df.set_index("format.filename")

    print(df.to_csv())


@typer_app.command()
def original(video_folder: Path):
    assert (
        video_folder.exists() and video_folder.is_dir()
    ), "Expecting video folder as first argument"

    ilids_video_xml_df = extract_clean_videos_from_xml_files(video_folder)

    print(ilids_video_xml_df.to_csv())


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
