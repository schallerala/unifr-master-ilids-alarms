import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Inspired from: https://github.com/Atze00/MoViNet-pytorch
# But also: https://github.com/tensorflow/models/tree/master/official/projects/movinet/configs/yaml
# TODO Make those configs configurable from the cli (and/or through a config file)
_movinet_transform_cfgs = dict(
    # tensorflow MoViNet validation input feature shape
    # - 50
    # - 172
    # - 172
    movineta0=dict(side_size=172, crop_size=172, num_frames=50),
    # tensorflow MoViNet validation input feature shape
    # - 50
    # - 172
    # - 172
    movineta1=dict(side_size=172, crop_size=172, num_frames=50),
    # tensorflow MoViNet validation input feature shape
    # - 50
    # - 224
    # - 224
    movineta2=dict(side_size=224, crop_size=224, num_frames=50),
    # tensorflow MoViNet validation input feature shape
    # - 64
    # - 256
    # - 256
    # 224 being the "intermediate" video side, therefore, no need to match the official
    # MoViNet validation shapes
    movineta3=dict(side_size=224, crop_size=224, num_frames=64),
    # tensorflow MoViNet validation input feature shape
    # - 80
    # - 290
    # - 290
    movineta4=dict(side_size=224, crop_size=224, num_frames=80),
    # tensorflow MoViNet validation input feature shape
    # - 120
    # - 320
    # - 320
    movineta5=dict(side_size=224, crop_size=224, num_frames=120),
)


def get_movinet_transform_config(model_name: str = "movineta0") -> Dict[str, int]:
    if model_name not in _movinet_transform_cfgs:
        logger.warning(
            f"Unknown MoViNet model name: {model_name}, returning empty configs"
        )
        return dict()

    return _movinet_transform_cfgs[model_name]
