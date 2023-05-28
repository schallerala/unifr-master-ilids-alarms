import dataclasses
from collections import OrderedDict
from pathlib import Path
from typing import Dict

import torch


@dataclasses.dataclass
class ActionClipStateDict:
    model_state_dict: Dict
    fusion_model_state_dict: Dict


def load_from_checkpoint(
    ckpt_file: Path, device=torch.device("cpu")
) -> ActionClipStateDict:
    """Inspired by: https://github.com/sallymmx/ActionCLIP/blob/HEAD/test.py#L146-L148"""
    assert ckpt_file.exists() and ckpt_file.is_file()

    checkpoint = torch.load(ckpt_file, map_location=device)

    # As the Fusion Model has been persisted to the disk while wrapped in a torch.nn.DataParallel module,
    # all the state dict keys have an additional "parent" level (or prefix).
    #
    # Example:
    #   Expected: 'frame_position_embeddings.weight'
    #   Actual:   'module.frame_position_embeddings.weight'
    #
    # Therefore, strip it off.
    fusion_model_state_dict = OrderedDict(
        {
            key.lstrip("module."): value
            for key, value in checkpoint["fusion_model_state_dict"].items()
        }
    )
    state_dicts = ActionClipStateDict(
        model_state_dict=checkpoint["model_state_dict"],
        fusion_model_state_dict=fusion_model_state_dict,
    )

    return state_dicts
