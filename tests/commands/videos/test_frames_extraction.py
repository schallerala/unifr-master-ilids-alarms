from pathlib import Path

import pytest
from hamcrest import *
from typer.testing import CliRunner

from ilids.cli.ffprobe import get_stream_info
from ilids.commands.videos.frames_extraction import typer_app

runner = CliRunner()


@pytest.mark.szte_files((Path("video") / "SZTEA101a.mov", "input_sequence"))
@pytest.mark.parametrize(
    "start_time,end_time,output_nb_frames",
    [("00:27:58", "00:28:59", 128), ("00:17:01", "00:17:48", 99)],
)
def test_extract__SZTEA101a_issue_frame_count(
    input_sequence: Path,
    tmp_path: Path,
    start_time: str,
    end_time: str,
    output_nb_frames: int,
):
    output_file = tmp_path / "output.mov"

    result = runner.invoke(
        typer_app,
        [str(input_sequence), start_time, end_time, "12", "-o", str(output_file)],
    )

    assert result.exit_code == 0

    assert output_file.exists()

    output_info = get_stream_info(output_file)

    assert len(output_info.streams) == 1

    assert_that(output_info.streams[0].avg_fps, is_(close_to(25, 0.1)))
    assert_that(output_info.streams[0].height, is_(224))
    assert_that(output_info.streams[0].width, is_(280))
    assert_that(output_info.streams[0].nb_frames, is_(output_nb_frames))
    assert_that(output_info.format.start_time, is_(close_to(0, 0.00001)))
    assert_that(output_info.format.duration, is_(close_to(output_nb_frames / 25, 0.01)))


def test_extract(create_sample_video, tmp_path: Path):
    # create a video of 2 minutes
    input_video_path = create_sample_video(120, (720, 576), 25, ".mov")

    output_file = tmp_path / "output.mov"

    result = runner.invoke(
        typer_app,
        [str(input_video_path), "00:00:46", "00:01:48", "12", "-o", str(output_file)],
    )

    assert result.exit_code == 0

    assert output_file.exists()

    output_info = get_stream_info(output_file)

    assert len(output_info.streams) == 1

    assert_that(output_info.streams[0].avg_fps, is_(close_to(25, 0.1)))
    assert_that(output_info.streams[0].height, is_(224))
    assert_that(output_info.streams[0].width, is_(280))
    assert_that(output_info.format.start_time, is_(close_to(0, 0.001)))
    new_duration = (48 + 60 - 46 + 1) / 12
    assert_that(output_info.format.duration, is_(close_to(new_duration, 0.1)))


@pytest.mark.long
def test_extract__long_video_with_start_time_0(create_sample_video, tmp_path: Path):
    # create a video of 80 minutes
    input_video_path = create_sample_video(80 * 60, (280, 224), 25, ".mov")

    output_file = tmp_path / "output.mov"

    result = runner.invoke(
        typer_app,
        [str(input_video_path), "01:12:46", "01:13:48", "12", "-o", str(output_file)],
    )

    assert result.exit_code == 0

    assert output_file.exists()

    output_info = get_stream_info(output_file)

    assert len(output_info.streams) == 1

    assert_that(output_info.streams[0].avg_fps, is_(close_to(25, 0.1)))
    assert_that(output_info.streams[0].height, is_(224))
    assert_that(output_info.streams[0].width, is_(280))
    assert_that(output_info.format.start_time, is_(close_to(0, 0.001)))
    new_duration = (48 + 60 - 46 + 1) / 12
    assert_that(output_info.format.duration, is_(close_to(new_duration, 0.1)))
