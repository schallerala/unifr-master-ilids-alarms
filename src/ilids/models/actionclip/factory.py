from pathlib import Path
from typing import Optional

import open_clip
import torch
from ilids.models.actionclip.constants import get_base_model_name_from_ckpt_path, get_input_frames_from_ckpt_path

from ilids.models.actionclip.model import ImageCLIP, TextCLIP
from ilids.models.actionclip.modules.visual_prompt import VisualPrompt
from ilids.models.actionclip.pretrained import load_from_checkpoint
from ilids.models.actionclip.transform import get_augmentation


def create_models_and_transforms(
    actionclip_pretrained_ckpt: Path,
    openai_model_name: Optional[str],  # ViT-B-32 ViT-B-16 (the ones that have a checkpoint for actionclip)
    extracted_frames: Optional[int],
    device: torch.device = torch.device("cpu"),
):
    # openai and extracted frames are optional and can try to extract the appropriate
    # value from the checkpoint path
    if openai_model_name is None:
        openai_model_name = get_base_model_name_from_ckpt_path(actionclip_pretrained_ckpt)
    if extracted_frames is None:
        extracted_frames = get_input_frames_from_ckpt_path(actionclip_pretrained_ckpt)

    model = open_clip.load_openai_model(
        openai_model_name, device=device
    )

    input_size = 224
    # Possible sim_header:
    #   Transf meanP  LSTM  Conv_1D  Transf_cls
    # However, choosing the one that worked the best in their work and apply it here too
    sim_header = "Transf"

    fusion_model = VisualPrompt(sim_header, model.state_dict(), extracted_frames).to(
        device=device
    )

    model_text = TextCLIP(model)
    model_image = ImageCLIP(model)

    if device == torch.device("cpu"):
        model_text.float()
        model_image.float()
    else:
        open_clip.model.convert_weights_to_fp16(
            model_text
        )  # Actually this line is unnecessary since clip by default already on float16
        open_clip.model.convert_weights_to_fp16(model_image)

    state_dicts = load_from_checkpoint(actionclip_pretrained_ckpt, device=device)

    model.load_state_dict(state_dicts.model_state_dict)
    fusion_model.load_state_dict(state_dicts.fusion_model_state_dict)

    preprocess_image = get_augmentation(input_size)

    return model_image, model_text, fusion_model, preprocess_image
