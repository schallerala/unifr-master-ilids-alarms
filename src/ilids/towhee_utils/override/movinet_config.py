import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Inspired from: https://github.com/Atze00/MoViNet-pytorch
# But also: https://github.com/tensorflow/models/tree/master/official/projects/movinet/configs/yaml
_movinet_transform_cfgs = dict(
    movineta0=dict(side_size=172, crop_size=172, num_frames=50),
    movineta1=dict(side_size=172, crop_size=172, num_frames=50),
    movineta2=dict(side_size=224, crop_size=224, num_frames=50),
    movineta3=dict(side_size=224, crop_size=224, num_frames=80),
    movineta4=dict(side_size=224, crop_size=224, num_frames=50),
    movineta5=dict(side_size=224, crop_size=224, num_frames=25),
)


def get_movinet_transform_config(model_name: str = "movineta0") -> Dict[str, int]:
    if model_name not in _movinet_transform_cfgs:
        logger.warning(
            f"Unknown MoViNet model name: {model_name}, returning empty configs"
        )
        return dict()

    return _movinet_transform_cfgs[model_name]
