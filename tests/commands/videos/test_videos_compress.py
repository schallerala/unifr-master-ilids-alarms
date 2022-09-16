from pathlib import Path

import pytest
from joblib import Parallel, cpu_count, delayed
from typer.testing import CliRunner

from ilids.commands.videos.videos_compress import typer_app

runner = CliRunner()


def test_all_default_all_cores(create_ilids_sample_video, tmp_path: Path):
    input_video_paths = Parallel(n_jobs=cpu_count())(
        delayed(create_ilids_sample_video)() for _ in range(4)
    )

    str_video_paths = [str(p) for p in input_video_paths]

    result = runner.invoke(
        typer_app,
        ["all", *str_video_paths, str(tmp_path), "-p", "prefix_all_"],
    )

    assert result.exit_code == 0

    for input_video_path in input_video_paths:
        output_file_path = tmp_path / f"prefix_all_{input_video_path.name}"

        assert output_file_path.exists()
        assert output_file_path.is_file()
        assert output_file_path.stat().st_size > 0

        output_file_path.unlink()
        # When creation of videos are done in parallel, they won't be cleaned properly, therefore
        # make sure to delete them here
        input_video_path.unlink()


def test_all_single_job(create_ilids_sample_video, tmp_path: Path):
    video_path = create_ilids_sample_video()

    result = runner.invoke(
        typer_app,
        [
            "all",
            str(video_path),
            str(tmp_path),
            "-p",
            "prefix_all_",
            "-j",
            1,
        ],
    )

    assert result.exit_code == 0

    output_file_path = tmp_path / f"prefix_all_{video_path.name}"

    assert output_file_path.exists()
    assert output_file_path.is_file()
    assert output_file_path.stat().st_size > 0


def test_all_fail__nonexistent_files(tmp_path: Path):
    result = runner.invoke(
        typer_app,
        [
            "all",
            str(tmp_path / "blabla.mov"),
            str(tmp_path),
            "-p",
            "prefix_all_",
        ],
    )

    assert result.exit_code == 1


def test_all_fail__nonexistent_output_folder(
    create_ilids_sample_video, tmp_path: Path
):
    input_video = create_ilids_sample_video()

    result = runner.invoke(
        typer_app,
        [
            "all",
            str(input_video),
            str(tmp_path / "output"),
            "-p",
            "prefix_all_",
        ],
    )

    assert result.exit_code == 1


def test_all_fail__output_is_not_folder(
    create_ilids_sample_video, tmp_path: Path
):
    input_video = create_ilids_sample_video()

    pseudo_output_folder = tmp_path / "file.txt"
    pseudo_output_folder.touch()

    result = runner.invoke(
        typer_app,
        [
            "all",
            str(input_video),
            str(pseudo_output_folder),
            "-p",
            "prefix_all_",
        ],
    )

    pseudo_output_folder.unlink()

    assert result.exit_code == 1


def test_all_fail__existing_output(
    create_ilids_sample_video, tmp_path: Path
):
    input_video = create_ilids_sample_video()

    result = runner.invoke(
        typer_app, ["all", str(input_video), str(tmp_path)]
    )

    assert result.exit_code == 1


def test_all_fail__fail_with_invalid_input_video(tmp_path: Path):
    input_video = tmp_path / "fake.mov"
    input_video.touch()

    result = runner.invoke(
        typer_app,
        [
            "all",
            str(input_video),
            str(tmp_path),
            "-p",
            "prefix_all_",
            "-j",
            1,
        ],
    )

    input_video.unlink()

    assert result.exit_code == 1


@pytest.mark.parametrize("prefix_option", ["-p", "--prefix"])
def test_single_with_prefix(
    create_ilids_sample_video, tmp_path: Path, prefix_option: str
):
    video_path = create_ilids_sample_video()

    result = runner.invoke(
        typer_app,
        ["single", str(video_path), str(tmp_path), prefix_option, "prefix_"],
    )

    assert result.exit_code == 0

    output_file_path = tmp_path / f"prefix_{video_path.name}"

    assert output_file_path.exists()
    assert output_file_path.is_file()
    assert output_file_path.stat().st_size > 0
