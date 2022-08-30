"""
Folder structure:

    SZTE/
    ├── calibration/        # Don't care, old .tif files
    ├── index-files/        # Html etc. files for their web interface, to browser and
    │                       #   filter the clips
    ├── video/              # Holds the videos in pairs with their xml files holding
    │   │                   #   video metadata
    │   ├── SZTEA101a.mov
    │   ├── SZTEA101a.xml       # Meta data for file SZTEA101a.mov.
    │   │                       #   Holds only minor meta on the video format itself
    │   ├── ... 64 pairs later
    │   ├── SZTEN203a.mov
    │   └── SZTEN203a.xml
    ├── i-LIDS Flyer.pdf        # General purpose 1 page flyer describing the different
    │                           #   i-LIDS datasets
    ├── index.xml               # Holds the perturbation annotations for the sequences
    │                           #   in the video/folder
    ├── Sterile Zone.pdf        # Short pdf describing the dataset and the structure of
    │                           #   the index.xml file
    └── User Guide.pdf          # Guide for the licensing, distribution, web app and more

This concentrates on the *.mov and *.xml in the **video** folder.
"""
import glob
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import typer

from ilids.models import DataFrameDescription
from ilids.models.ffprobe import FfprobeVideo
from ilids.subcommand.ffprobe import get_stream_info
from ilids.utils.xml import read_xml

_VIDEOS_CSV_FIELDS_DESCRIPTION = """\
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


def _extract_videos_from_xml_files(video_folder: Path) -> pd.DataFrame:
    """Expected to find for each video, its corresponding XML file:

    Example:
        Video file: SZTEN203a.mov
        XML file: SZTEN203a.xml"""

    xml_files = glob.glob(str(video_folder / "*.xml"))

    # 1. Read each XML file and pop their root element to join them as a list
    parsed_xmls = [read_xml(Path(f)).pop("GeeVSClip") for f in xml_files]

    # 2. Return as a DataFrame without any manipulation of the data
    return pd.json_normalize(parsed_xmls)


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


def _cleanup_videos_data(df: pd.DataFrame) -> pd.DataFrame:
    # Replace MS like path to POSIX notation
    df["VideoPath"] = df["VideoPath"].str.replace(
        "E:\\\\video\\\\", "./video/", regex=True
    )

    return df


def _ffprobe_videos(video_folder: Path, video_extension: str) -> List[FfprobeVideo]:
    video_files = glob.glob(str(video_folder / f"*.{video_extension.lstrip('.')}"))

    ffprobe_results = [get_stream_info(Path(video_file)) for video_file in video_files]

    return ffprobe_results


def _merge_xml_video_df_and_ffprobes(
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


def _extract_video_descriptions(
    video_folder: Path, video_extension: str
) -> DataFrameDescription:
    ilids_video_xml_df = _extract_videos_from_xml_files(video_folder)
    ilids_video_xml_df = _keep_relevant_videos_columns(ilids_video_xml_df)
    ilids_video_xml_df = _cleanup_videos_data(ilids_video_xml_df)
    ffprobes = _ffprobe_videos(video_folder, video_extension)

    return DataFrameDescription(
        description=_VIDEOS_CSV_FIELDS_DESCRIPTION,
        data_frame=_merge_xml_video_df_and_ffprobes(
            ilids_video_xml_df, ffprobes, video_extension
        ),
    )


def extract_video_metadata_szte() -> None:
    pass


if __name__ == "__main__":
    typer.run(extract_video_metadata_szte)
