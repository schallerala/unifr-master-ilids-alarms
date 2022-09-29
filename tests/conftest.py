import os
import subprocess
import time
from functools import partial
from pathlib import Path
from typing import Callable, List, Tuple

import pytest


@pytest.fixture()
def szte_path() -> Path:
    return Path(os.getcwd()) / "data" / "SZTE"


@pytest.fixture()
def sztr_path() -> Path:
    return Path(os.getcwd()) / "data" / "SZTR"

@pytest.fixture()
def ckpt_path() -> Path:
    return Path(os.getcwd()) / "ckpt"


def _data_file_marker_builder(request, marker_name: str, parent_folder: Path):
    marker = request.node.get_closest_marker(marker_name)
    if marker:
        for file, variable_name in marker.args:
            if (parent_folder / Path(file)).exists():
                request.node.fixturenames.append(variable_name)
                request.node.funcargs[variable_name] = parent_folder / Path(file)
            elif Path(file).exists():
                request.node.add_marker(
                    pytest.mark.parametrize(variable_name, [Path(file)])
                )
            else:
                pytest.skip(f"skipped as file {str(parent_folder / file)} is missing")


@pytest.fixture(autouse=True)
def add_data_files_markers(request, szte_path: Path, sztr_path: Path, ckpt_path: Path):
    _data_file_marker_builder(request, "szte_files", szte_path)
    _data_file_marker_builder(request, "sztr_files", sztr_path)
    _data_file_marker_builder(request, "ckpt_files", ckpt_path)


def _generate_sample_video(
    duration: float,
    dimension: Tuple[int, int],
    fps: int,
    extension: str,
    output_folder: Path,
) -> Path:
    width, height = dimension

    filename = f"{time.perf_counter_ns()}.{extension.lstrip('.')}"

    output_file = output_folder / filename
    process = subprocess.Popen(
        [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=duration={duration}:size={width}x{height}:rate={fps}",
            str(output_file),
        ]
    )

    process.wait()

    assert process.returncode == 0, "Failed to generate a sample video with ffmpeg"

    return output_file


@pytest.fixture()
def create_sample_video(
    request, tmp_path: Path
) -> Callable[[float, Tuple[int, int], int, str], Path]:
    created_videos: List[Path] = []

    def _generate_sample_video_wrapper(
        duration: float, dimension: Tuple[int, int], fps: int, extension: str
    ) -> Path:
        new_video_path = _generate_sample_video(
            duration, dimension, fps, extension, output_folder=tmp_path
        )

        created_videos.append(new_video_path)

        return new_video_path

    def _delete_all_videos():
        for video_path in created_videos:
            video_path.unlink(missing_ok=True)

    request.addfinalizer(_delete_all_videos)

    return _generate_sample_video_wrapper


@pytest.fixture()
def create_ilids_sample_video(create_sample_video) -> Callable[[], Path]:
    return partial(create_sample_video, 10, (720, 576), 25, ".mov")


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "szte_files(...files): skip test if one of the given file name doesn't exists",
    )
    config.addinivalue_line(
        "markers",
        "sztr_files(...files): skip test if one of the given file name doesn't exists",
    )
    config.addinivalue_line(
        "markers",
        "ckpt_files(...files): skip test if one of the given file name doesn't exists inside the ./ckpt folder",
    )
