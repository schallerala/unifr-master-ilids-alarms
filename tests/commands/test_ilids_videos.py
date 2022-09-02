import glob
import io
from pathlib import Path

import pandas as pd
import pytest
from hamcrest import *
from typer.testing import CliRunner

from ilids.commands.sztr.extract_video_metadata_sztr import typer_app

runner = CliRunner()


def test_no_input(tmp_path):
    result = runner.invoke(
        typer_app,
        ["ffprobe", Path(tmp_path) / "input.txt"],
    )
    assert result.exit_code == 1


@pytest.mark.sztr_files(("video", "video_folder"))
def test_invoke(video_folder: Path):
    result = runner.invoke(typer_app, ["ffprobe", str(video_folder)])
    assert result.exit_code == 0, result.stderr

    df = pd.read_csv(io.StringIO(result.stdout))
    assert_that(len(df), is_(len(glob.glob(str(video_folder / "*.mov")))))
    assert_that(len(df.columns), greater_than_or_equal_to(5))


def test_invoke_meta():
    result = runner.invoke(typer_app, ["meta"])
    assert result.exit_code == 0, result.stderr

    assert_that(
        len(result.stdout.splitlines()), greater_than_or_equal_to(2)
    )  # 2 being the number of "fields"
