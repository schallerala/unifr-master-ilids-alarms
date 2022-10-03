# Code for "ActionCLIP: ActionCLIP: A New Paradigm for Action Recognition"
# arXiv:
# Mengmeng Wang, Jiazheng Xing, Yong Liu

from ilids.models.actionclip.datasets.transforms_ss import *


def get_augmentation(input_size: int = 224):
    input_mean = [0.48145466, 0.4578275, 0.40821073]
    input_std = [0.26862954, 0.26130258, 0.27577711]

    scale_size = input_size * 256 // 224

    unique = torchvision.transforms.Compose(
        [GroupScale(scale_size), GroupCenterCrop(input_size)]
    )

    common = torchvision.transforms.Compose(
        [
            Stack(roll=False),
            ToTorchFormatTensor(div=True),
            GroupNormalize(input_mean, input_std),
        ]
    )
    return torchvision.transforms.Compose([unique, common])
