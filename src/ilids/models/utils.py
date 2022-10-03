import torch.nn as nn
from open_clip.model import Attention


def fix_convert_weights_to_fp16(model: nn.Module):
    """open_clip seems to miss the conversion of certain submodules. Try to fix it and apply model parameters to fp16"""

    def _convert_weights_to_fp16(l):
        if isinstance(l, nn.LayerNorm):
            if l.elementwise_affine:
                l.weight.data = l.weight.data.half()
                l.bias.data = l.bias.data.half()

    model.apply(_convert_weights_to_fp16)
