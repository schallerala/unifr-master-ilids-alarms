from collections import defaultdict
from functools import reduce
from multiprocessing import cpu_count
from pathlib import Path
from typing import List

import towhee
from hamcrest import *
from joblib import Parallel, delayed
from towhee import register
from towhee.operator import PyOperator
from towhee.types import VideoFrame

import ilids.towhee_utils.cached_video_decoder


@register(name="frame_counter", output_schema=["count"])
class FrameCounter(PyOperator):
    def __init__(self):
        super().__init__()
        self._calls_count = defaultdict(int)

    def __call__(self, path: str, video: List[VideoFrame]) -> int:
        self._calls_count[path] += 1

        assert len([1 for count in self._calls_count.values() if count > 1]) == 0

        return len(video)


def test_cached_video_decoder(create_ilids_sample_video, tmp_path: Path):
    video_paths = Parallel(n_jobs=cpu_count())(
        delayed(create_ilids_sample_video)() for _ in range(2)
    )

    str_video_paths = [str(p) for p in video_paths]

    cached_video_decoder = (
        towhee.dc["path"](str_video_paths)
        .video_decode.ffmpeg["path", "frames"]()
        .ilids.cached_video_decoder[("path", "frames"), "frames"]()
    )

    count_data_collections: List[towhee.DataCollection] = [
        cached_video_decoder.frame_counter[("path", "frames"), "count"]()
        .select["count"]()
        .to_dc()
        for _ in range(4)
    ]

    assert len(count_data_collections) == 4

    joined_entities: List[towhee.Entity] = reduce(
        lambda i, j: i + j, count_data_collections
    ).to_list()

    assert len(joined_entities) == 4 * 2

    assert_that(
        joined_entities, only_contains(has_property("count", is_(equal_to(10 * 25))))
    )
