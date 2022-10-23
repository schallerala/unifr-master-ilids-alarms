from typing import Dict

import numpy as np
import pandas as pd
import torch.nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from ilids.models.actionclip.model import ImageCLIP
from ilids.models.actionclip.modules.visual_prompt import VisualPrompt


def extract_actionclip_sequences_features(
    image_model: ImageCLIP,
    fusion_model: VisualPrompt,
    sequences_dataloader: DataLoader,
    extracted_frames: int,
    normalize_features: bool,
    device: torch.device,
) -> pd.DataFrame:
    image_model.eval()
    fusion_model.eval()

    extracted_features: Dict[str, np.ndarray] = dict()

    for iii, (frames_batch, paths_batch) in enumerate(tqdm(sequences_dataloader)):
        frames_batch = frames_batch.view(
            (-1, extracted_frames, 3) + frames_batch.size()[-2:]
        )
        b, t, c, h, w = frames_batch.size()
        images_input = frames_batch.to(device).view(-1, c, h, w)

        # To speed up computation with cuda, during the model creation, we initialise its
        # weight to float16.
        # But for other device, like CPU, nothing is done. Therefore, no need to autocast.
        # autocast: https://github.com/mlfoundations/open_clip/pull/80#issuecomment-1118621323
        enable_autocast = False if device == torch.device("cpu") else True
        with torch.autocast(
            device_type=device.type, enabled=enable_autocast
        ), torch.no_grad():
            images_features = image_model(images_input).view(
                b, t, -1
            )  # Tensor: (B, Features), Features = 512

            images_features = fusion_model(
                images_features
            )  # Tensor: (B, Features), Features = 512

        if normalize_features:
            images_features /= images_features.norm(
                dim=-1, keepdim=True
            )  # Tensor: (T, Features), Features = 512

        images_features = images_features.detach().cpu().numpy()

        for path, image_features in zip(paths_batch, images_features):
            extracted_features[path] = image_features

    return pd.DataFrame.from_dict(extracted_features, orient="index")
