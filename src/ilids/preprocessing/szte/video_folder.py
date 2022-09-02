"""
This concentrate on parsing of xml files in the video folder of SZTE and also merging its results
with ffprobe executions.
"""
import glob
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from ilids.models import FfprobeVideo
from ilids.utils.xml import read_xml

VIDEOS_CSV_FIELDS_DESCRIPTION = """\
VideoPath:      POSIX path from the root of the SZTE folder
                [example: './video/SZTEA101a.mov']
VideoLength:    Frame count in the clip, for example, './video/SZTEA101a.mov' has
                a frame rate of approx. 25 and a duration of 37'12":
                (minutes * 60 + seconds) * frame rate = (37 * 60 + 12) * 25 = 55'800
                (difference is due to the fact that the last second is not complete)
                [example: 55789]
Name:           Name of the video file without extension
                [example: 'SZTEA101a']
Datarate:       _Not certain to get what it expresses_
                [example: 54900]
AspectRatio:    Ratio between width and height expressed in a string seperated by a
                colon like this 'W:H'
                [example: '4:3']
format.X.Y.Z:   Fields extracted using ffprobe CLI
stream.X.Y.Z:   Fields extracted using ffprobe CLI concerning the single video stream
                of the video\
"""


def _keep_relevant_videos_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Most of the other columns are empty or aren't representative of
    # any useful information

    # df.drop(
    #     [
    #         "DatabaseID", "FolderID", "VideoTrack", "KeyPath", "KeyLength", "A1Path",
    #         "A1Length", "A1Slip", "A1Track", "A2Path", "A2Length", "A2Slip", "A2Track",
    #         "A3Path", "A3Length", "A3Slip", "A3Track", "A4Path", "A4Length", "A4Slip",
    #         "A4Track", "VBIPath", "VBILength", "VBITrack", "Description", "Category",
    #         "Agency", "UsageAvailable", "Usage",
    #         "...",
    #     ]
    # )  # better select to ones to keep
    return df[["VideoPath", "VideoLength", "Name", "Datarate", "AspectRatio"]]


def _cleanup_video_path_posix_style(df: pd.DataFrame) -> pd.DataFrame:
    # Replace MS like path to POSIX notation
    df["VideoPath"] = df["VideoPath"].str.replace(
        "E:\\\\video\\\\", "./video/", regex=True
    )

    return df


def merge_xml_video_df_and_ffprobes(
    ilids_video_xml_df: pd.DataFrame, ffprobes: List[FfprobeVideo], video_extension: str
) -> pd.DataFrame:
    assert len(ilids_video_xml_df) == len(ffprobes)

    def dict_and_flatten_video_streams(video: FfprobeVideo) -> Dict[str, Any]:
        """As only a SINGLE video stream is expected in the videos, squeeze the stream list
        to then convert in DataFrame
        """
        dic: Dict[str, Any] = video.dict()
        streams = dic.pop("streams")

        assert len(streams) == 1, "Expected a unique stream in the given video"

        dic["stream"] = streams[0]

        return dic

    ffprobe_objs = [dict_and_flatten_video_streams(video) for video in ffprobes]
    ffprobe_df = pd.json_normalize(ffprobe_objs)

    # Add a column to *join* the 2 DataFrames
    ffprobe_df["Name"] = ffprobe_df["format.filename"].str.removesuffix(
        f".{video_extension.lstrip('.')}"
    )

    merged_df = ilids_video_xml_df.set_index("Name").join(ffprobe_df.set_index("Name"))

    return merged_df


def extract_videos_from_xml_files(video_folder: Path) -> pd.DataFrame:
    """Expected to find for each video, its corresponding XML file:

    Example:
        Video file: SZTEN203a.mov
        XML file: SZTEN203a.xml"""

    xml_files = glob.glob(str(video_folder / "*.xml"))

    # 1. Read each XML file and pop their root element to join them as a list
    parsed_xmls = [read_xml(Path(f)).pop("GeeVSClip") for f in xml_files]

    # 2. Return as a DataFrame without any manipulation of the data
    return pd.json_normalize(parsed_xmls)


def extract_clean_videos_from_xml_files(video_folder: Path) -> pd.DataFrame:
    """Apply a few manipulation of the raw DataFrame for cleaner usage"""
    df = extract_videos_from_xml_files(video_folder)

    df = _keep_relevant_videos_columns(df)
    df = _cleanup_video_path_posix_style(df)

    return df
