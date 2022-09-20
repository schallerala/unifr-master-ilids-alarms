import csv
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy
import torch
from einops import rearrange
from towhee import register
from towhee.models.movinet.movinet import create_model
from towhee.models.utils.video_transforms import get_configs, transform_video
from towhee.operator.base import NNOperator
from towhee.types.video_frame import VideoFrame

from ilids.towhee_utils.override.movinet_config import get_movinet_transform_config

log = logging.getLogger()


@register(name="ilids/movinet", output_schema=["labels", "scores", "features"])
class Movinet(NNOperator):
    """
    Generate a list of class labels given a video input data.
    Default labels are from [Kinetics600 Dataset](https://deepmind.com/research/open-source/kinetics).
    Args:
        model_name (`str="movineta0"`):
            Supported model names:
            - movineta0
            - movineta1
            - movineta2
            - movineta3
            - movineta4
            - movineta5
        causal (`bool=False`):
            Use causal = True to use the model with stream buffer, causal = False will use standard
            convolutions
        skip_preprocess (`bool=False`):
            Flag to skip video transforms.
        classmap (`dict=None`):
            The dictionary maps classes to integers. If not given, use the standard Kinetics 600
            class map.
        topk (`int=5`):
            The number of classification labels to be returned (ordered by possibility from high to low).
    """

    def __init__(
        self,
        model_name: str = "movineta0",
        causal: bool = False,
        skip_preprocess: bool = False,
        classmap: Dict[int, str] = None,
        topk: int = 5,
    ):
        super().__init__(framework="pytorch")
        self.model_name = model_name
        self.causal = causal
        self.skip_preprocess = skip_preprocess
        self.topk = topk
        self.dataset_name = "kinetics_600"
        if classmap is None:
            class_file = os.path.join(
                str(Path(__file__).parent), "kinetics_600" + ".csv"
            )
            csvFile = open(class_file, "r")
            reader = csv.reader(csvFile)
            self.classmap = {}
            for item in reader:
                if reader.line_num == 1:
                    continue
                self.classmap[int(item[0])] = item[1]
            csvFile.close()
        else:
            self.classmap = classmap
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = create_model(
            model_name=model_name,
            pretrained=True,
            causal=self.causal,
            device=self.device,
        )
        self.input_mean = [0.43216, 0.394666, 0.37645]
        self.input_std = [0.22803, 0.22145, 0.216989]
        self.transform_cfgs = get_configs(
            side_size=172,
            crop_size=172,
            num_frames=13,
            mean=self.input_mean,
            std=self.input_std,
        )
        self.transform_cfgs.update(**get_movinet_transform_config(model_name))
        self.model.eval()

    def save_model(self):
        """
        Save model to local.
        """
        raise NotImplementedError

    def supported_model_names(self) -> List[str]:
        return [
            "movineta0",
            "movineta1",
            "movineta2",
            "movineta3",
            "movineta4",
            "movineta5",
        ]

    def __call__(self, video: List[VideoFrame]):
        """
        Args:
            video (`List[VideoFrame]`):
                Video path in string.

        Returns:
            (labels, scores, features)
                A tuple of lists (labels, scores, features, head_output).
        """
        # Convert list of towhee.types.Image to numpy.ndarray in float32
        video = numpy.stack(
            [img.astype(numpy.float32) / 255.0 for img in video], axis=0
        )
        assert len(video.shape) == 4
        video = rearrange(video, "t w h c -> c t w h")
        # video = video.transpose(3, 0, 1, 2)  # twhc -> ctwh

        # Transform video data given configs
        if self.skip_preprocess:
            self.transform_cfgs.update(num_frames=None)

        data = transform_video(video=video, **self.transform_cfgs)
        inputs = data.to(self.device)[None, ...]

        self.model.clean_activation_buffers()
        feats = self.model.forward_features(inputs)
        outs = self.model.head(feats)

        features = outs.flatten(1).cpu().squeeze(0).detach().numpy()

        post_act = torch.nn.Softmax(dim=1)
        preds = post_act(outs)
        pred_scores, pred_classes = preds.topk(k=self.topk)
        labels = [self.classmap[int(i)] for i in pred_classes[0]]
        scores = [round(float(x), 5) for x in pred_scores[0]]

        return labels, scores, features
