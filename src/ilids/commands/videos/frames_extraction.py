import logging
import math
from datetime import date, datetime, time, timedelta
from pathlib import Path
from time import gmtime, strftime
from typing import Optional

import numpy as np
import typer

from ilids.cli.ffmpeg import scale_compress_select_sequence
from ilids.cli.ffprobe import get_stream_info

typer_app = typer.Typer()

logger = logging.getLogger(__name__)


def _parse_output(input_video: Path, start: timedelta, output: Optional[Path]) -> Path:
    default_output_filename = f"{input_video.stem}_{strftime('%H_%M_%S', gmtime(start.total_seconds()))}{input_video.suffix}"

    if output is not None:
        if output.is_dir():
            return output / default_output_filename
        else:
            return output

    return input_video.parent / default_output_filename


def _get_fps(input_video: Path) -> float:
    logger.info("Read input video to get fps...")
    info = get_stream_info(input_video)

    assert len(info.streams) == 1

    return info.streams[0].avg_fps


def _trivial_frame_selection(stride: int, total_frames: int):
    return list(range(0, total_frames, stride)) + (
        [] if (total_frames - 1) % stride == 0 else [total_frames - 1]
    )


@typer_app.command()
def extract(
    input_video: Path,
    start_time: str,
    end_time: str,
    frame_stride: int,
    fps: Optional[float] = typer.Option(None, "--fps", "-r"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    overwrite: bool = typer.Option(False, "--overwrite", "-y"),
) -> None:
    if not input_video.exists() or not input_video.is_file():
        raise ValueError("Expected a file as first argument")

    assert frame_stride > 0

    start = datetime.combine(date.min, time.fromisoformat(start_time)) - datetime.min
    end = datetime.combine(date.min, time.fromisoformat(end_time)) - datetime.min

    assert start >= timedelta.min
    assert end > timedelta.min
    assert start < end

    total_seconds = (end - start).total_seconds()

    output = _parse_output(input_video, start, output)

    if not overwrite and output.exists():
        raise ValueError(f"Use -y option to overwrite the existing {str(output)}")

    fps = fps or _get_fps(input_video)
    assert fps is not None and fps > 0

    frames_sequence_to_extract_0_shifted = _trivial_frame_selection(
        frame_stride, math.ceil(total_seconds * fps)
    )
    frames_sequence_to_extract = (
        (np.array(frames_sequence_to_extract_0_shifted) + (start.total_seconds() * fps))
        .astype(int)
        .tolist()
    )

    returncode = scale_compress_select_sequence(
        input_video, output, frames_sequence_to_extract, math.ceil(fps), overwrite
    )

    assert returncode == 0, "Issue while extract sequence from input video"
