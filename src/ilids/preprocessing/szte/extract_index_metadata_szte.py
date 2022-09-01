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
import json
from pathlib import Path

import pandas as pd
import typer

from ilids.models.szte import IlidsLibrary
from ilids.utils.dict import deep_get
from ilids.utils.xml import read_xml

typer_app = typer.Typer()

"""Commands structure:

    szte-index
       ├── all              # avoids parsing 3 times the index.xml file
       ├── clips            # print out the clips information
       ├── alarms           # print out the alarms information
       └── distractions      # print out the distractions
"""


def _read_index_xml(index: Path) -> IlidsLibrary:
    index_xml = read_xml(index)

    # Extract only part of the produced structure (IlidsLibraryIndex.Library)
    ilids_library_xml = deep_get(index_xml, "IlidsLibraryIndex.Library")

    library = IlidsLibrary.parse_obj(ilids_library_xml)

    return library


# def _change_clip_filename_extension(lib: IlidsLibrary, extension_from: str, extension_to: str) -> IlidsLibrary:
#     extension_from = f".{extension_from.lstrip('.')}"
#     extension_to = extension_to.lstrip('.')

#     for clip in lib.clip:
#         if clip.filename.endswith(extension_from):
#             clip.filename = f"{clip.filename.lstrip(extension_from)}.{extension_to}"

#     return lib


@typer_app.command(name="all")
def all_cli(  # only to avoid shadowing builtin method
    index_xml: Path,
    meta_output: Path,
    clips_output: Path,
    alarms_output: Path,
    distractions_output: Path,
    force: bool = typer.Option(
        False, "--force", "-f", help="Force override existing files"
    ),
) -> None:
    assert index_xml.exists(), "Expecting an existing index.xml file"

    assert (
        meta_output.parent.exists() and meta_output.parent.is_dir()
    ), "Expecting parent of meta.json to exist and be a folder"
    assert (
        clips_output.parent.exists() and clips_output.parent.is_dir()
    ), "Expecting parent of clips.csv to exist and be a folder"
    assert (
        alarms_output.parent.exists() and alarms_output.parent.is_dir()
    ), "Expecting parent of alarms.csv to exist and be a folder"
    assert (
        distractions_output.parent.exists() and distractions_output.parent.is_dir()
    ), "Expecting parent of distractions.csv to exist and be a folder"

    if not force:
        assert (
            not meta_output.exists()
        ), "meta.json exists already, use --force, -f to override"
        assert (
            not clips_output.exists()
        ), "clips.csv exists already, use --force, -f to override"
        assert (
            not alarms_output.exists()
        ), "alarms.csv exists already, use --force, -f to override"
        assert (
            not distractions_output.exists()
        ), "distractions.csv exists already, use --force, -f to override"

    lib = _read_index_xml(index_xml)

    with open(meta_output, "w") as meta_fb:
        json.dump(
            dict(scenario=lib.scenario, dataset=lib.dataset, version=lib.libversion),
            meta_fb,
        )

    clips_df = pd.json_normalize(lib.get_clips_information_dict()).set_index("filename")
    clips_df.to_csv(clips_output)

    alarms_df = pd.json_normalize(lib.flat_map_alarms_dict()).set_index("filename")
    alarms_df.to_csv(alarms_output)

    distractions_df = pd.json_normalize(lib.flat_map_distractions_dict()).set_index(
        "filename"
    )
    distractions_df.to_csv(distractions_output)


@typer_app.command()
def clips(index_xml: Path) -> None:
    lib = _read_index_xml(index_xml)

    clips_df = pd.json_normalize(lib.get_clips_information_dict()).set_index("filename")
    print(clips_df.to_csv())


@typer_app.command()
def alarms(index_xml: Path) -> None:
    lib = _read_index_xml(index_xml)

    alarms_df = pd.json_normalize(lib.flat_map_alarms_dict()).set_index("filename")
    print(alarms_df.to_csv())


@typer_app.command()
def distractions(index_xml: Path) -> None:
    lib = _read_index_xml(index_xml)

    distractions_df = pd.json_normalize(lib.flat_map_distractions_dict()).set_index(
        "filename"
    )
    print(distractions_df.to_csv())


if __name__ == "__main__":
    typer_app()
