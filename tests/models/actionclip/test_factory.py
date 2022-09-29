import os.path
from collections.abc import Callable
from pathlib import Path

import pytest
from hamcrest import *

import torch

from ilids.models.actionclip.factory import create_models_and_transforms


@pytest.mark.ckpt_files((Path("actionclip") / "vit-b-16-16f.pt", "actionclip_ckpt"))
def test_create_models_and_transforms(actionclip_ckpt: Path):
    model_image, model_text, fusion_model, preprocess_image = create_models_and_transforms(actionclip_pretrained_ckpt=actionclip_ckpt, openai_model_name="ViT-B-16")

    assert_that(model_image, is_(all_of(not_(None), instance_of(torch.nn.Module))))
    assert_that(model_text, is_(all_of(not_(None), instance_of(torch.nn.Module))))
    assert_that(fusion_model, is_(all_of(not_(None), instance_of(torch.nn.Module))))
    assert_that(preprocess_image, is_(all_of(not_(None), instance_of(Callable))))
