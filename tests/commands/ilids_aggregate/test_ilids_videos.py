import glob
import io
from pathlib import Path

import pandas as pd
import pytest
from hamcrest import *
from typer.testing import CliRunner

from ilids.commands.ilids_aggregate.ilids_videos import typer_app

runner = CliRunner()


def test_no_input(tmp_path):
    result = runner.invoke(
        typer_app,
        ["ffprobe", Path(tmp_path) / "input.txt"],
    )
    assert result.exit_code == 1


@pytest.mark.szte_files(("video", "szte_video_folder"))
@pytest.mark.sztr_files(("video", "sztr_video_folder"))
def test_invoke(szte_video_folder: Path, sztr_video_folder: Path):
    result = runner.invoke(
        typer_app, ["ffprobe", str(szte_video_folder), str(sztr_video_folder)]
    )
    assert result.exit_code == 0, result.stderr

    df = pd.read_csv(io.StringIO(result.stdout))
    szte_videos = len(glob.glob(str(szte_video_folder / "*.mov")))
    sztr_videos = len(glob.glob(str(sztr_video_folder / "*.mov")))
    assert_that(len(df), is_(szte_videos + sztr_videos))
    assert_that(len(df.columns), greater_than_or_equal_to(25))


def test_invoke_meta():
    result = runner.invoke(typer_app, ["meta"])
    assert result.exit_code == 0, result.stderr

    assert_that(
        len(result.stdout.splitlines()), greater_than_or_equal_to(2)
    )  # 2 being the number of "fields"
