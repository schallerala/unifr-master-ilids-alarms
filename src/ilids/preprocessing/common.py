import glob
from pathlib import Path
from typing import List

from joblib import Parallel, cpu_count, delayed

from ilids.cli.ffprobe import get_stream_info
from ilids.models import FfprobeVideo


def ffprobe_videos(video_folder: Path, video_extension: str) -> List[FfprobeVideo]:
    video_files = glob.glob(str(video_folder / f"*.{video_extension.lstrip('.')}"))

    ffprobe_results = Parallel(n_jobs=cpu_count())(
        delayed(get_stream_info)(Path(video_file)) for video_file in video_files
    )

    return ffprobe_results
