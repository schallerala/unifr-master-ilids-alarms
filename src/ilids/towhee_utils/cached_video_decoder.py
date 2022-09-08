from logging import getLogger
from typing import Dict, List

from towhee import register
from towhee.operator import PyOperator
from towhee.types import VideoFrame

logger = getLogger(__name__)


@register(name="ilids/cached_video_decoder")
class CachedVideoDecoder(PyOperator):
    """Directly decode the video and keep them in memory"""

    def __init__(self):
        super().__init__()
        self.latest_frames: Dict[str, List[VideoFrame]] = dict()

    def __call__(self, path: str, video: List[VideoFrame]) -> List[VideoFrame]:
        if path in self.latest_frames:
            logger.debug(f"Returning cached frames for {path}")
            return self.latest_frames[path]

        self.latest_frames[path] = list(video)

        return self.latest_frames[path]
