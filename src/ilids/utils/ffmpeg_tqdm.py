"""
A ffmpeg download wrapper for ffmpeg and tqdm.

Wrapper was created in favor of [animdl](https://github.com/justfoolingaround/animdl.git)
and since the developer doesn't care about you copying and pasting this code somewhere,
you may do it. No need for credit. You might feel guilty though.

Hope **your** project becomes easier.
"""

# adaptation from https://gist.github.com/justfoolingaround/6b9857626d862563ff11e0d90f8428f2

import logging
import os
import re
import shutil
import subprocess
from collections import defaultdict
from typing import Dict, Optional

from tqdm import tqdm

executable = "ffmpeg"
has_ffmpeg = lambda: bool(shutil.which(executable))

FFMPEG_EXTENSIONS = ["mpd", "m3u8", "m3u"]


def parse_ffmpeg_duration(dt: str) -> float:
    """
    Converts ffmpeg duration to seconds.

    Returns
    ---

    `float`
    """
    hour, minute, seconds = (float(_) for _ in dt.split(":"))
    return hour * (60**2) + minute * 60 + seconds


def iter_audio(stderr):
    """
    Goes over the audio part of the ffmpeg output and gets the mapping index and
    the frequency.

    Returns
    ---

    `Generator[tuple(str, int)]`

    """

    def it():
        """
        A generator, that is made for sorting and sending to another generator.
        """
        for match in re.finditer(b"Stream #(\\d+):(\\d+): Audio:.+ (\\d+) Hz", stderr):
            program, stream_id, freq = (_.decode() for _ in match.groups())
            yield "{}:a:{}".format(program, stream_id), int(freq)

    yield from sorted(it(), key=lambda x: x[1], reverse=True)


def analyze_stream(logger: logging.Logger, url: str, headers: Optional[Dict] = None):
    """
    Converts the output of `ffmpeg -i $URL` to a partial stream info default dict.

    In logging level DEBUG, it shows the ffmpeg output.

    Returns
    ---

    `collections.defaultdict`

    """
    if headers is None:
        headers = dict()

    info = defaultdict(lambda: defaultdict(lambda: defaultdict(defaultdict)))

    args = [executable, "-hide_banner"]

    if headers:
        args.extend(
            ("-headers", "\r\n".join("{}:{}".format(k, v) for k, v in headers.items()))
        )

    args.extend(("-i", url))

    logger.debug("Calling PIPE child process for ffmpeg: {}".format(args))
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    stderr = b"".join(iter(process.stdout))

    duration = re.search(b"Duration: ((?:\\d+:)+\\d+)", stderr)
    if duration:
        info["duration"] = parse_ffmpeg_duration(duration.group(1).decode())

    audio = [*iter_audio(stderr)]

    for match in re.finditer(b"Stream #(\\d+):(\\d+): Video: .+x(\\d+)", stderr):
        program, stream_index, resolution = (int(_.decode()) for _ in match.groups())
        info["streams"][program][stream_index]["quality"] = resolution
        info["streams"][program][stream_index]["audio"] = audio

    return info


def get_last(iterable):
    """
    Gets the last element from the iterable. Pretty self-explanatory.
    """
    expansion = [*iterable]
    if expansion:
        return expansion[-1]


def ffmpeg_to_tqdm(
    logger: logging.Logger,
    process: subprocess.Popen,
    duration: int,
    tqdm_desc: str = "FFMPEG execution",
    tqdm_position: Optional[int] = None,
) -> subprocess.CompletedProcess:
    """
    tqdm wrapper for a ffmpeg process.

    Takes a logger `logger`, the ffmpeg child process `process`, duration of stream
    `duration` and the output file's name `outfile_name`

    This uses the simple concept, stream reading using `iter`, after which it takes
    the current time, converts it into seconds and shows the full progress bar.

    In logging level DEBUG, it shows the ffmpeg output.

    Returns
    ---

    `subprocess.Popen` but completed

    """
    progress_bar = tqdm(
        desc=tqdm_desc, total=duration, unit="segment", position=tqdm_position
    )
    previous_span = 0

    for line in process.stdout:
        logger.debug("[ffmpeg] {}".format(line.strip()))

        current = get_last(re.finditer("\\stime=((?:\\d+:)+\\d+)", line))
        if current:
            in_seconds = parse_ffmpeg_duration(current.group(1)) - previous_span
            previous_span += in_seconds
            progress_bar.update(in_seconds)

    progress_bar.update(duration)
    progress_bar.close()

    return process
