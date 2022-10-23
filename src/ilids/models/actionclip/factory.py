from pathlib import Path

import open_clip
import torch

from ilids.models.actionclip.model import ImageCLIP, TextCLIP
from ilids.models.actionclip.modules.visual_prompt import VisualPrompt
from ilids.models.actionclip.pretrained import load_from_checkpoint
from ilids.models.actionclip.transform import get_augmentation


def create_models_and_transforms(
    actionclip_pretrained_ckpt: Path,
    openai_model_name: str,  # ViT-B-32 ViT-B-16 (the ones that have a checkpoint for actionclip)
    extracted_frames: int,
    device: torch.device = torch.device("cpu"),
    jit: bool = False,
):
    model = open_clip.load_openai_model(
        openai_model_name, device=device, jit=jit
    )  # Must set jit=False for training  ViT-B/32 TODO: try jit=True

    input_size = 224  # TODO
    sim_header = "Transf"  # Transf   meanP  LSTM  Conv_1D  Transf_cls # TODO

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
