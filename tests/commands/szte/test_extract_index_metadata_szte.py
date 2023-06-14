import io
import json
from pathlib import Path
from typing import List

import pandas as pd
import pytest
from hamcrest import *
from typer.testing import CliRunner

from ilids.commands.szte.extract_index_metadata_szte import typer_app

runner = CliRunner()


def _tmp_file_builder(tmp_path: Path, filename: str):
    f = Path(tmp_path) / filename
    yield f
    f.unlink(missing_ok=True)


@pytest.fixture()
def meta_tmp_file(tmp_path):
    yield from _tmp_file_builder(tmp_path, "meta.json")


@pytest.fixture()
def clips_tmp_file(tmp_path):
    yield from _tmp_file_builder(tmp_path, "clips.csv")


@pytest.fixture()
def alarms_tmp_file(tmp_path):
    yield from _tmp_file_builder(tmp_path, "alarms.csv")


@pytest.fixture()
def distractions_tmp_file(tmp_path):
    yield from _tmp_file_builder(tmp_path, "distractions.csv")


def test_no_input(
    tmp_path,
    meta_tmp_file: Path,
    clips_tmp_file: Path,
    alarms_tmp_file: Path,
    distractions_tmp_file: Path,
):
    result = runner.invoke(
        typer_app,
        [
            "all",
            Path(tmp_path) / "input.txt",
            str(meta_tmp_file),
            str(clips_tmp_file),
            str(alarms_tmp_file),
            str(distractions_tmp_file),
        ],
    )
    assert result.exit_code == 1


@pytest.mark.parametrize(
    "paths_to_create",
    (
        [True, False, False, False],
        [True, True, False, False],
        [True, True, True, False],
        [True, True, True, True],
    ),
)
def test_need_force_to_overwrite(tmp_path, paths_to_create: List[bool]):
    outputs = [
        (Path(tmp_path) / f"{i}.txt") for i, _create in enumerate(paths_to_create)
    ]
    for i, create in enumerate(paths_to_create):
        if create:
            outputs[i].touch()

    index = Path(tmp_path) / "input.txt"
    index.touch()

    result = runner.invoke(typer_app, ["all", str(index), *[str(p) for p in outputs]])
    assert result.exit_code == 1


@pytest.mark.szte_files(("index.xml", "index"))
@pytest.mark.parametrize(
    "force_arg",
    ("-f", "--force"),
)
def test_force_and_overwrite(
    index: Path,
    meta_tmp_file: Path,
    clips_tmp_file: Path,
    alarms_tmp_file: Path,
    distractions_tmp_file: Path,
    force_arg,
):
    meta_tmp_file.touch()
    clips_tmp_file.touch()
    alarms_tmp_file.touch()
    distractions_tmp_file.touch()

    result = runner.invoke(
        typer_app,
        [
            "all",
            force_arg,
            str(index),
            str(meta_tmp_file),
            str(clips_tmp_file),
            str(alarms_tmp_file),
            str(distractions_tmp_file),
        ],
    )
    assert result.exit_code == 0, result.stderr

    assert meta_tmp_file.exists() and meta_tmp_file.is_file()
    assert clips_tmp_file.exists() and clips_tmp_file.is_file()
    assert alarms_tmp_file.exists() and alarms_tmp_file.is_file()
    assert distractions_tmp_file.exists() and distractions_tmp_file.is_file()

    with open(meta_tmp_file, "r") as f:
        meta = json.load(f)
        assert_that(meta, has_key("scenario"))
        assert_that(meta, has_key("version"))
        assert_that(meta, has_key("dataset"))

    with open(clips_tmp_file, "r") as f:
        df = pd.read_csv(f)
        assert_that(len(df), greater_than(10))
        assert_that(len(df.columns), greater_than_or_equal_to(9))

    with open(alarms_tmp_file, "r") as f:
        df = pd.read_csv(f)
        assert_that(len(df), greater_than(10))
        assert_that(len(df.columns), greater_than_or_equal_to(8))

    with open(distractions_tmp_file, "r") as f:
        df = pd.read_csv(f)
        assert_that(len(df), greater_than(10))
        assert_that(len(df.columns), greater_than_or_equal_to(2))


@pytest.mark.szte_files(("index.xml", "index"))
def test_invoke_all(
    index: Path,
    meta_tmp_file: Path,
    clips_tmp_file: Path,
    alarms_tmp_file: Path,
    distractions_tmp_file: Path,
):
    result = runner.invoke(
        typer_app,
        [
            "all",
            str(index),
            str(meta_tmp_file),
            str(clips_tmp_file),
            str(alarms_tmp_file),
            str(distractions_tmp_file),
        ],
    )
    assert result.exit_code == 0, result.stderr

    assert meta_tmp_file.exists() and meta_tmp_file.is_file()
    assert clips_tmp_file.exists() and clips_tmp_file.is_file()
    assert alarms_tmp_file.exists() and alarms_tmp_file.is_file()
    assert distractions_tmp_file.exists() and distractions_tmp_file.is_file()

    with open(meta_tmp_file, "r") as f:
        meta = json.load(f)
        assert_that(meta, has_key("scenario"))
        assert_that(meta, has_key("version"))
        assert_that(meta, has_key("dataset"))

    with open(clips_tmp_file, "r") as f:
        df = pd.read_csv(f)
        assert_that(len(df), greater_than(10))
        assert_that(len(df.columns), greater_than_or_equal_to(9))

    with open(alarms_tmp_file, "r") as f:
        df = pd.read_csv(f)
        assert_that(len(df), greater_than(10))
        assert_that(len(df.columns), greater_than_or_equal_to(8))

    with open(distractions_tmp_file, "r") as f:
        df = pd.read_csv(f)
        assert_that(len(df), greater_than(10))
        assert_that(len(df.columns), greater_than_or_equal_to(2))


@pytest.mark.szte_files(("index.xml", "index"))
def test_invoke_clips(index: Path):
    result = runner.invoke(
        typer_app,
        [
            "clips",
            str(index),
        ],
    )
    assert result.exit_code == 0, result.stderr

    df = pd.read_csv(io.StringIO(result.stdout))
    assert_that(len(df), greater_than(10))
    assert_that(len(df.columns), greater_than_or_equal_to(9))


@pytest.mark.szte_files(("index.xml", "index"))
def test_invoke_alarms(index: Path):
    result = runner.invoke(
        typer_app,
        [
            "alarms",
            str(index),
        ],
    )
    assert result.exit_code == 0, result.stderr

    df = pd.read_csv(io.StringIO(result.stdout))
    assert_that(len(df), greater_than(10))
    assert_that(len(df.columns), greater_than_or_equal_to(8))


@pytest.mark.szte_files(("index.xml", "index"))
def test_invoke_distractions(index: Path):
    result = runner.invoke(
        typer_app,
        [
            "distractions",
            str(index),
        ],
    )
    assert result.exit_code == 0, result.stderr

    df = pd.read_csv(io.StringIO(result.stdout))
    assert_that(len(df), greater_than(10))
    assert_that(len(df.columns), greater_than_or_equal_to(2))


@pytest.mark.szte_files(("index.xml", "index"))
def test_invoke_meta(index: Path):
    result = runner.invoke(
        typer_app,
        [
            "meta",
            str(index),
        ],
    )
    assert result.exit_code == 0, result.stderr

    meta = json.loads(result.stdout)
    assert_that(meta, has_key("scenario"))
    assert_that(meta, has_key("version"))
    assert_that(meta, has_key("dataset"))
