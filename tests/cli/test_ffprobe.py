import glob
from pathlib import Path

import pytest
from hamcrest import *

from ilids.cli.ffprobe import get_stream_info


@pytest.mark.szte_files(("video", "video_folder"))
def test_ffprobe(video_folder: Path):
    first_video = glob.glob(str(video_folder / "*.mov"))[0]

    assert Path(first_video).is_file()

    ffprobe = get_stream_info(Path(first_video))

    assert_that(len(ffprobe.streams), is_(1))
    assert_that(ffprobe.format.filename, ends_with(".mov"))
