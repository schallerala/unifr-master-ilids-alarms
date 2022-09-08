import numpy
import torch
import towhee
from hamcrest import *
from towhee import ops
from towhee.engine import OperatorRegistry
from towhee.functional.entity import Entity
from utils.matchers import is_tensor_with_shape

from ilids.towhee_utils.override.movinet import Movinet


def test_get_movinet_override():
    override_of_movinet = ops.ilids.movinet()

    assert_that(override_of_movinet, is_not(None))

    override_of_movinet = OperatorRegistry.resolve("ilids/movinet")

    assert_that(override_of_movinet, is_not(None))
    assert_that(override_of_movinet.metainfo, instance_of(dict))
    assert_that(override_of_movinet.metainfo, has_key("output_schema"))
    assert_that(override_of_movinet.metainfo["output_schema"].labels, is_not(None))
    assert_that(override_of_movinet.metainfo["output_schema"].scores, is_not(None))
    assert_that(override_of_movinet.metainfo["output_schema"].features, is_not(None))


def test_get_override_movinet_from_chain_call():
    entity: Entity = (
        towhee.glob["path"]("data/sequences/SZTR_video_SZTRA102b13_00_00_20_TP.mp4")
        .video_decode.ffmpeg["path", "frames"]()
        .ilids.movinet["frames", ("labels", "scores", "features")](
            model_name="movineta0"
        )
        .select["path", "labels", "scores", "features"]()
    )[
        0
    ]  # get first as only executing on a single video

    assert_that(entity, has_property("labels", has_length(5)))
    assert_that(entity, has_property("scores", has_length(5)))
    assert_that(
        entity,
        has_property("features", all_of(instance_of(numpy.ndarray), has_length(600))),
    )
