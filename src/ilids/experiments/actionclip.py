import torch.nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from ilids.models.actionclip.model import ImageCLIP
from ilids.models.actionclip.modules.visual_prompt import VisualPrompt


def extract_actionclip_sequences_features(
    image_model: ImageCLIP,
    fusion_model: VisualPrompt,
    sequences_dataloader: DataLoader,
    device: torch.device,
):
    image_model.eval()
    fusion_model.eval()

    with torch.no_grad():
        for iii, frames_batch in enumerate(tqdm(sequences_dataloader)):
            extracted_frames_config = 8
            frames_batch = frames_batch.view(
                (-1, extracted_frames_config, 3) + frames_batch.size()[-2:]
            )
            b, t, c, h, w = frames_batch.size()
            image_input = frames_batch.to(device).view(-1, c, h, w)
            image_features = image_model(image_input).view(b, t, -1)
            image_features = fusion_model(image_features)
            image_features /= image_features.norm(dim=-1, keepdim=True)

            # TODO persist features
