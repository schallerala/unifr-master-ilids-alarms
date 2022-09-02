import glob
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from joblib import Parallel, cpu_count, delayed

from ilids.cli.ffprobe import get_stream_info
from ilids.models import FfprobeVideo


def ffprobe_videos(video_folder: Path, video_extension: str) -> List[FfprobeVideo]:
    video_files = glob.glob(str(video_folder / f"*.{video_extension.lstrip('.')}"))

    ffprobe_results = Parallel(n_jobs=cpu_count())(
        delayed(get_stream_info)(Path(video_file)) for video_file in video_files
    )

    return ffprobe_results


def _dict_and_flatten_video_streams(video: FfprobeVideo) -> Dict[str, Any]:
    """As only a SINGLE video stream is expected in the videos, squeeze the stream list
    to then convert in DataFrame
    """
    dic: Dict[str, Any] = video.dict()
    streams = dic.pop("streams")

    assert len(streams) == 1, "Expected a unique stream in the given video"

    dic["stream"] = streams[0]

    return dic


def ffprobe_videos_to_df(ffprobes: List[FfprobeVideo]) -> pd.DataFrame:
    ffprobe_objs = [_dict_and_flatten_video_streams(video) for video in ffprobes]
    ffprobe_df = pd.json_normalize(ffprobe_objs)

    return ffprobe_df
