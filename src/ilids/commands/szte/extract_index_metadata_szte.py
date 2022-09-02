import json
from pathlib import Path

import pandas as pd
import typer

from ilids.preprocessing.szte.index_xml import read_index_xml

typer_app = typer.Typer()

"""Commands structure:

    szte-index
       ├── all              # avoids parsing 3 times the index.xml file
       ├── clips            # print out the clips information
       ├── alarms           # print out the alarms information
       ├── distractions     # print out the distractions
       └── meta             # print details on the library
"""


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

    lib = read_index_xml(index_xml)

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
    lib = read_index_xml(index_xml)

    clips_df = pd.json_normalize(lib.get_clips_information_dict()).set_index("filename")
    print(clips_df.to_csv())


@typer_app.command()
def alarms(index_xml: Path) -> None:
    lib = read_index_xml(index_xml)

    alarms_df = pd.json_normalize(lib.flat_map_alarms_dict()).set_index("filename")
    print(alarms_df.to_csv())


@typer_app.command()
def distractions(index_xml: Path) -> None:
    lib = read_index_xml(index_xml)

    distractions_df = pd.json_normalize(lib.flat_map_distractions_dict()).set_index(
        "filename"
    )
    print(distractions_df.to_csv())


@typer_app.command()
def meta(index_xml: Path) -> None:
    lib = read_index_xml(index_xml)

    print(
        json.dumps(
            dict(scenario=lib.scenario, dataset=lib.dataset, version=lib.libversion),
        )
    )


if __name__ == "__main__":
    typer_app()
