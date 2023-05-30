import os
import subprocess
from pathlib import Path

from ilids.datamodels import FfprobeVideo


# add information from ffprobe (inspiration: https://gist.github.com/nrk/2286511)
def _get_stream_info_with_ffprobe(video_path: Path) -> str:
    """Execute ffprobe on the given file and returns the unparsed json"""
    command = [
        "ffprobe",
        "-v",
        "quiet",  # loglevel quiet: Show nothing at all; be silent.
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        os.path.basename(video_path),
    ]

    ffprobe_process = subprocess.Popen(
        command, cwd=video_path.parent, stdout=subprocess.PIPE
    )
    ffprobe_process.wait()

    stdout, stderr = ffprobe_process.communicate()

    assert ffprobe_process.returncode == 0, f"ffprobe didn't run successfully {stderr.decode()}"

    return stdout.decode()


def get_stream_info(video_path: Path) -> FfprobeVideo:
    raw_json = _get_stream_info_with_ffprobe(video_path)

    return FfprobeVideo.parse_raw(raw_json)
