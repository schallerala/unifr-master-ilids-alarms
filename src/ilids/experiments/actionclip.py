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
    device: torch.device,
) -> pd.DataFrame:
    image_model.eval()
    fusion_model.eval()

    extracted_features: Dict[str, np.ndarray] = dict()

    with torch.no_grad():
        for iii, (frames_batch, paths_batch) in enumerate(tqdm(sequences_dataloader)):
            # On CUDA, half precision
            if device.type == "cuda":
                frames_batch = frames_batch.half()

            frames_batch = frames_batch.view(
                (-1, extracted_frames, 3) + frames_batch.size()[-2:]
            )
            b, t, c, h, w = frames_batch.size()
            images_input = frames_batch.to(device).view(-1, c, h, w)

            images_features = image_model(images_input).view(b, t, -1)

            images_features = fusion_model(images_features)
            images_features /= images_features.norm(
                dim=-1, keepdim=True
            )  # Tensor: (T, Features), Features = 512

            images_features = images_features.detach().cpu().numpy()

            for path, image_features in zip(paths_batch, images_features):
                extracted_features[path] = image_features

    return pd.DataFrame.from_dict(extracted_features, orient="index")
