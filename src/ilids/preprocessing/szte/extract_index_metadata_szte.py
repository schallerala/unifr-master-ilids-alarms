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

This concentrates on the **index.xml** file.
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


def extract_video_metadata_szte() -> None:
    pass


if __name__ == "__main__":
    typer.run(extract_video_metadata_szte)
