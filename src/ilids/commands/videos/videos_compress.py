from pathlib import Path
from typing import List, Optional

import typer
from joblib import cpu_count, delayed
from typer import Option

from ilids.cli.ffmpeg import ffmpeg_scale_compress
from ilids.utils.progress_parallel import ProgressParallel

typer_app = typer.Typer()


@typer_app.command(name="all")
def command_all(
    input_videos: List[Path],
    output_folder: Path,
    output_file_prefix: Optional[str] = Option(None, "--prefix", "-p"),
    output_file_suffix: Optional[str] = Option(None, "--suffix", "-s"),
    overwrite: bool = Option(False, "--overwrite", "-y"),
    jobs: Optional[int] = Option(None, "--jobs", "-j"),
) -> None:
    nonexistent_files = list(
        map(
            lambda non_existing_file: str(non_existing_file),
            filter(
                lambda input_video: not input_video.exists()
                or not input_video.is_file(),
                input_videos,
            ),
        )
    )
    if len(nonexistent_files) > 0:
        raise ValueError(f"Invalid inputs: {', '.join(nonexistent_files)}")

    if not output_folder.exists():
        raise ValueError("Output folder doesn't exists")
    if not output_folder.is_dir():
        raise ValueError("Output isn't a folder")

    output_videos = [
        output_folder
        / "".join(
            [
                output_file_prefix or "",
                video_path.stem,
                output_file_suffix or "",
                video_path.suffix,
            ]
        )
        for video_path in input_videos
    ]

    if not overwrite:
        existing_outputs = list(
            map(
                lambda existing_output: existing_output.name,
                filter(lambda out: out.exists(), output_videos),
            )
        )
        if len(existing_outputs) > 0:
            raise ValueError(
                f"Use -y option to overwrite the existing outputs: {', '.join(existing_outputs)}"
            )

    jobs = jobs or cpu_count()

    def _exit_instantly_ffmpeg_scale_compress(i, *args, **kwargs):
        returncode = ffmpeg_scale_compress(
            *args, tqdm_position=(i % jobs) + 1, **kwargs
        )

        if returncode == 0:
            return True
        else:
            print(f"Issue to scale and compress {' '.join([str(arg) for arg in args])}")
            return False

    print(f"Starting {jobs} concurrent jobs...")

    successes = ProgressParallel(
        n_jobs=jobs,
        position=0,
        desc="Processed video",
        total=len(input_videos),
        unit="segment",
    )(
        delayed(_exit_instantly_ffmpeg_scale_compress)(
            i, input_video, output_video, overwrite
        )
        for i, (input_video, output_video) in enumerate(
            zip(input_videos, output_videos)
        )
    )

    assert any(successes), "All encoding and scaling failed"

    print("Done successfully")


@typer_app.command()
def single(
    input_video: Path,
    output_folder: Path,
    output_file_prefix: Optional[str] = Option(None, "--prefix", "-p"),
    output_file_suffix: Optional[str] = Option(None, "--suffix", "-s"),
    overwrite: bool = Option(False, "--overwrite", "-y"),
) -> None:
    if not input_video.exists() or not input_video.is_file():
        raise ValueError("Expecting an existing input video")

    if not output_folder.exists():
        raise ValueError("Output folder doesn't exists")
    if not output_folder.is_dir():
        raise ValueError("Output isn't a folder")

    output_video = output_folder / "".join(
        [
            output_file_prefix or "",
            input_video.stem,
            output_file_suffix or "",
            input_video.suffix,
        ]
    )

    if not overwrite and output_video.exists():
        raise ValueError(
            f"Use -y option to overwrite the existing output: {str(output_video)}"
        )

    returncode = ffmpeg_scale_compress(input_video, output_video, overwrite)

    assert (
        returncode == 0
    ), f"Issue to scale and compress {str(input_video)} to {str(output_video)}"

    print("Done successfully")
