import json
from pathlib import Path

import pandas as pd
import typer

from ilids.preprocessing.szte.index_xml import read_index_xml as read_szte_index_xml
from ilids.preprocessing.sztr.index_xml import read_index_xml as read_sztr_index_xml

typer_app = typer.Typer()

"""Commands structure:

    ilids-indexes
       ├── all              # avoids parsing 3 times the index.xml file
       ├── clips            # print out the clips information
       ├── alarms           # print out the alarms information
       ├── distractions     # print out the distractions
       └── meta             # print details on the library

Will merge the result of the sub-commands 'szte-index' and 'sztr-index'
"""


@typer_app.command(name="all")
def all_cli(  # only to avoid shadowing builtin method
    szrte_index_xml: Path,
    szrtr_index_xml: Path,
    meta_output: Path,
    clips_output: Path,
    alarms_output: Path,
    distractions_output: Path,
    force: bool = typer.Option(
        False, "--force", "-f", help="Force override existing files"
    ),
) -> None:
    assert szrte_index_xml.exists(), "Expecting an existing SZTE index.xml file"
    assert szrtr_index_xml.exists(), "Expecting an existing SZTR index.xml file"

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

    lib_szte = read_szte_index_xml(szrte_index_xml)
    lib_sztr = read_sztr_index_xml(szrtr_index_xml)

    with open(meta_output, "w") as meta_fb:
        json.dump(
            dict(
                szte=dict(
                    dict(
                        scenario=lib_szte.scenario,
                        dataset=lib_szte.dataset,
                        version=lib_szte.libversion,
                    ),
                ),
                sztr=dict(
                    dict(
                        scenario=lib_sztr.scenario,
                        dataset=lib_sztr.dataset,
                        version=lib_sztr.libversion,
                    ),
                ),
            ),
            meta_fb,
        )

    szte_clips_df = pd.json_normalize(lib_szte.get_clips_information_dict()).set_index(
        "filename"
    )
    szte_clips_df.index = "SZTE/video/" + szte_clips_df.index
    sztr_clips_df = pd.json_normalize(lib_sztr.get_clips_information_dict()).set_index(
        "filename"
    )
    sztr_clips_df.index = "SZTR/video/" + sztr_clips_df.index
    clips_df = pd.concat([szte_clips_df, sztr_clips_df])
    clips_df.to_csv(clips_output)

    szte_alarms_df = pd.json_normalize(lib_szte.flat_map_alarms_dict()).set_index(
        "filename"
    )
    szte_alarms_df.index = "SZTE/video/" + szte_alarms_df.index
    sztr_alarms_df = pd.json_normalize(lib_sztr.flat_map_alarms_dict()).set_index(
        "filename"
    )
    sztr_alarms_df.index = "SZTR/video/" + sztr_alarms_df.index
    alarms_df = pd.concat([szte_alarms_df, sztr_alarms_df])
    alarms_df.to_csv(alarms_output)

    szte_distractions_df = pd.json_normalize(
        lib_szte.flat_map_distractions_dict()
    ).set_index("filename")
    szte_distractions_df.index = "SZTE/video/" + szte_distractions_df.index
    sztr_distractions_df = pd.json_normalize(
        lib_sztr.flat_map_distractions_dict()
    ).set_index("filename")
    sztr_distractions_df.index = "SZTR/video/" + sztr_distractions_df.index
    distractions_df = pd.concat([szte_distractions_df, sztr_distractions_df])
    distractions_df.to_csv(distractions_output)


@typer_app.command()
def clips(
    szrte_index_xml: Path,
    szrtr_index_xml: Path,
) -> None:
    assert szrte_index_xml.exists(), "Expecting an existing SZTE index.xml file"
    assert szrtr_index_xml.exists(), "Expecting an existing SZTR index.xml file"

    lib_szte = read_szte_index_xml(szrte_index_xml)
    lib_sztr = read_sztr_index_xml(szrtr_index_xml)

    szte_clips_df = pd.json_normalize(lib_szte.get_clips_information_dict()).set_index(
        "filename"
    )
    szte_clips_df.index = "SZTE/video/" + szte_clips_df.index
    sztr_clips_df = pd.json_normalize(lib_sztr.get_clips_information_dict()).set_index(
        "filename"
    )
    sztr_clips_df.index = "SZTR/video/" + sztr_clips_df.index
    clips_df = pd.concat([szte_clips_df, sztr_clips_df])
    print(clips_df.to_csv())


@typer_app.command()
def alarms(
    szrte_index_xml: Path,
    szrtr_index_xml: Path,
) -> None:
    assert szrte_index_xml.exists(), "Expecting an existing SZTE index.xml file"
    assert szrtr_index_xml.exists(), "Expecting an existing SZTR index.xml file"

    lib_szte = read_szte_index_xml(szrte_index_xml)
    lib_sztr = read_sztr_index_xml(szrtr_index_xml)

    szte_alarms_df = pd.json_normalize(lib_szte.flat_map_alarms_dict()).set_index(
        "filename"
    )
    szte_alarms_df.index = "SZTE/video/" + szte_alarms_df.index
    sztr_alarms_df = pd.json_normalize(lib_sztr.flat_map_alarms_dict()).set_index(
        "filename"
    )
    sztr_alarms_df.index = "SZTR/video/" + sztr_alarms_df.index
    alarms_df = pd.concat([szte_alarms_df, sztr_alarms_df])
    print(alarms_df.to_csv())


@typer_app.command()
def distractions(
    szrte_index_xml: Path,
    szrtr_index_xml: Path,
) -> None:
    assert szrte_index_xml.exists(), "Expecting an existing SZTE index.xml file"
    assert szrtr_index_xml.exists(), "Expecting an existing SZTR index.xml file"

    lib_szte = read_szte_index_xml(szrte_index_xml)
    lib_sztr = read_sztr_index_xml(szrtr_index_xml)

    szte_distractions_df = pd.json_normalize(
        lib_szte.flat_map_distractions_dict()
    ).set_index("filename")
    szte_distractions_df.index = "SZTE/video/" + szte_distractions_df.index
    sztr_distractions_df = pd.json_normalize(
        lib_sztr.flat_map_distractions_dict()
    ).set_index("filename")
    sztr_distractions_df.index = "SZTR/video/" + sztr_distractions_df.index
    distractions_df = pd.concat([szte_distractions_df, sztr_distractions_df])
    print(distractions_df.to_csv())


@typer_app.command()
def meta(
    szrte_index_xml: Path,
    szrtr_index_xml: Path,
) -> None:
    assert szrte_index_xml.exists(), "Expecting an existing SZTE index.xml file"
    assert szrtr_index_xml.exists(), "Expecting an existing SZTR index.xml file"

    lib_szte = read_szte_index_xml(szrte_index_xml)
    lib_sztr = read_sztr_index_xml(szrtr_index_xml)

    print(
        json.dumps(
            dict(
                szte=dict(
                    dict(
                        scenario=lib_szte.scenario,
                        dataset=lib_szte.dataset,
                        version=lib_szte.libversion,
                    ),
                ),
                sztr=dict(
                    dict(
                        scenario=lib_sztr.scenario,
                        dataset=lib_sztr.dataset,
                        version=lib_sztr.libversion,
                    ),
                ),
            )
        )
    )
