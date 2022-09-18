import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from ilids.utils.ffmpeg_tqdm import analyze_stream, ffmpeg_to_tqdm


def _ffmpeg_select(frames_sequence: List[int]) -> str:
    """Produce a string to be used with the FFMPEG command and its "select" argument.

    In most cases, it would be necessary to correct the timestamp of the frames, use setpts filter.
    Else, if start of timing will produce unexpected results.

    :param frames_sequence: linear or not list of frames to extract.
                            Example: 0, 12, 24, 36, 48, 60, ...
                            or:      6, 23, 27, 42, 50, 68, ...
    :param setpts_filter: from FFMPEG manual page:
                            "setpts" filter, which only sets timestamps and otherwise passes the frames unchanged
                          It is expected to be smaller than 1 in can less frames are selected and it is wished to
                          speed up the video.
                          Usually, it is expected to get 1/FRAMES_SKIP
                          Example: *0.25* (for a FRAMES_SKIP of 4)
    :return: string to be used to run the FFMPEG command for the "select" argument like: ffmpeg -i SZTRA201a08_224.mp4 -vf select='eq(n\,0)+eq(n\,12)+eq(n\,24)+eq(n\,36)+eq(n\,48)+eq(n\,60), setpts=0.08333333333*PTS' -an SZTRA201a08_224_12_random.mp4
    """
    # eq(n\\,0)+eq(n\\,12)+eq(n\\,24)+eq(n\\,36)+eq(n\\,48)
    eq_chain = "+".join([f"eq(n\,{n})" for n in frames_sequence])

    return eq_chain


def _ffmpeg_setpts(fps: int) -> str:
    # change the 'setpts' filter to correct the new time base of the extracted frames
    # References:
    #   - https://youtu.be/ckCuy7dmyPI
    #   - http://underpop.online.fr/f/ffmpeg/help/setpts_002c-asetpts.htm.gz
    return f"N/({fps}*TB)"


# Adapted from CLIP4Clip: https://github.com/ArrowLuo/CLIP4Clip/blob/master/preprocess/compress_video.py
# but don't change the frame rate as be which to have different frame selection strategies
# use ffmpeg_to_tqdm helper
def ffmpeg_scale_compress(
    input_video_path: Path,
    output_video_path: Path,
    overwrite: bool = False,
    new_short_side: int = 224,
    video_codec: str = "libx264",
    tqdm_position: Optional[int] = None,
) -> int:
    logger = logging.getLogger(f"ffmpeg-{str(output_video_path)}")
    logger.debug("Using ffmpeg to scale and compress and extract sub sequence")

    stream_info = analyze_stream(logger, str(input_video_path))

    # to avoid carriage return ('\r') in ffmpeg output, to mess with the reading of the
    # progress, use 'universal_newlines' argument
    # https://github.com/chriskiehl/Gooey/issues/495#issuecomment-614991802
    ffmpeg_process = subprocess.Popen(
        f"ffmpeg -i {str(input_video_path)} "
        f"-vf \"scale='if(gt(a,1),trunc(oh*a/2)*2,{new_short_side})':'if(gt(a,1),{new_short_side},trunc(ow*a/2)*2)'\" "
        f"-map 0:v "
        # -vcodec
        #       get list of codecs with ffmpeg -codecs
        f"-vcodec {video_codec} "
        f"{'-y' if overwrite else ''} "
        f"{str(output_video_path)}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

    ffmpeg_to_tqdm(
        logger,
        ffmpeg_process,
        duration=stream_info.get("duration", 0),
        tqdm_desc=f"FFMPEG scale down to {new_short_side} and encode with {video_codec}",
        tqdm_position=tqdm_position,
    )

    ffmpeg_process.wait()

    return ffmpeg_process.returncode


# Same as above, but also extract frames
# and directly extract a sequence of frames
def scale_compress_select_sequence(
    input_video_path: Path,
    output_video_path: Path,
    frames_sequence: List[int],
    fps: int,
    overwrite: bool = False,
    new_short_side: int = 224,
    video_codec: str = "libx264",
) -> int:
    logger = logging.getLogger(f"ffmpeg-{str(output_video_path)}")
    logger.debug("Using ffmpeg to scale and compress and extract sub sequence")

    stream_info = analyze_stream(logger, str(input_video_path))

    # to avoid carriage return ('\r') in ffmpeg output, to mess with the reading of the
    # progress, use 'universal_newlines' argument
    # https://github.com/chriskiehl/Gooey/issues/495#issuecomment-614991802
    ffmpeg_process = subprocess.Popen(
        # -frames:v
        #       -frames[:stream_specifier] framecount (output,per-stream)
        #           Stop writing to the stream after framecount frames.
        # -vcodec
        #       get list of codecs with ffmpeg -codecs
        f"ffmpeg -i {str(input_video_path)} "
        f"-frames:v {len(frames_sequence)} "
        f"-vf \"select={_ffmpeg_select(frames_sequence)},setpts={_ffmpeg_setpts(fps)},scale='if(gt(a,1),trunc(oh*a/2)*2,{new_short_side})':'if(gt(a,1),{new_short_side},trunc(ow*a/2)*2)'\" "
        f"-map 0:v "
        f"-vcodec {video_codec} "
        f"{'-y' if overwrite else ''} "
        f"{str(output_video_path)}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

    ffmpeg_to_tqdm(
        logger,
        ffmpeg_process,
        duration=stream_info.get("duration"),
        tqdm_desc=f"FFMPEG scale down to {new_short_side}, select frames and encode with {video_codec}",
    )

    ffmpeg_process.wait()

    return ffmpeg_process.returncode
