import glob
import io
from pathlib import Path

import pandas as pd
import pytest
from hamcrest import *
from typer.testing import CliRunner

from ilids.commands.szte.extract_video_metadata_szte import typer_app

runner = CliRunner()

_ALL_COMMANDS = ["merged", "original", "ffprobe"]


@pytest.mark.parametrize(
    "command",
    _ALL_COMMANDS,
)
def test_no_input(tmp_path, command):
    result = runner.invoke(
        typer_app,
        [command, Path(tmp_path) / "input.txt"],
    )
    assert result.exit_code == 1


@pytest.mark.szte_files(("video", "video_folder"))
@pytest.mark.parametrize("command", _ALL_COMMANDS)
def test_invoke(video_folder: Path, command):
    result = runner.invoke(
        typer_app,
        [
            command,
            str(video_folder),
        ],
    )
    assert result.exit_code == 0, result.stderr

    df = pd.read_csv(io.StringIO(result.stdout))
    assert_that(len(df), is_(len(glob.glob(str(video_folder / "*.mov")))))
    assert_that(len(df.columns), greater_than_or_equal_to(5))


def test_invoke_meta():
    result = runner.invoke(
        typer_app,
        [
            "meta",
        ],
    )
    assert result.exit_code == 0, result.stderr

    assert_that(
        len(result.stdout.splitlines()), greater_than_or_equal_to(7)
    )  # 7 being the number of "fields"
