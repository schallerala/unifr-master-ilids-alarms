# Code for "ActionCLIP: ActionCLIP: A New Paradigm for Action Recognition"
# arXiv:
# Mengmeng Wang, Jiazheng Xing, Yong Liu
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import PIL
import torch
import torch.utils.data as data
from decord import VideoReader, cpu
from numpy.random import randint
from PIL import Image


class ActionDataset(data.Dataset):
    def __init__(
        self,
        sequences_details_file: Path,
        transform,
        frames_to_extract: int,  # Example: 8, 16, 32
        seg_length: int = 1,  # TODO not sure what it does
        random_shift: bool = False,
        index_bias: int = 1,
    ):
        self.frames_to_extract = frames_to_extract  # 8
        self.seg_length = seg_length  # 1
        self.transform = transform
        self.random_shift = random_shift
        self.index_bias = index_bias

        self._sequences_df = pd.read_csv(sequences_details_file)
        # require at least those 2 columns
        assert (
            len(
                self._sequences_df.columns.intersection(
                    pd.Index(["sequence", "frame_count"])
                )
            )
            == 2
        )

        # remove all sequences with not enough frames
        self._sequences_df = self._sequences_df[
            self._sequences_df["frame_count"] >= self.frames_to_extract
        ]
        self._sequences_df.reset_index(inplace=True)

    @property
    def _total_length(self) -> int:
        return self.frames_to_extract * self.seg_length

    def _random_sample_indices(self, record_num_frames: int) -> np.ndarray:
        if record_num_frames <= self._total_length:
            offsets = np.concatenate(
                (
                    np.arange(record_num_frames),
                    randint(
                        record_num_frames, size=self._total_length - record_num_frames
                    ),
                )
            )
            return np.sort(offsets) + self.index_bias
        offsets = list()
        ticks = [
            i * record_num_frames // self.frames_to_extract
            for i in range(self.frames_to_extract + 1)
        ]

        for i in range(self.frames_to_extract):
            tick_len = ticks[i + 1] - ticks[i]
            tick = ticks[i]
            if tick_len >= self.seg_length:
                tick += randint(tick_len - self.seg_length + 1)
            offsets.extend([j for j in range(tick, tick + self.seg_length)])
        return np.array(offsets) + self.index_bias

    def _sample_indices(self, record_num_frames: int) -> np.ndarray:
        if self.frames_to_extract == 1:
            return np.array([record_num_frames // 2], dtype=np.uint) + self.index_bias

        if record_num_frames <= self._total_length:
            return (
                np.array(
                    [
                        i * record_num_frames // self._total_length
                        for i in range(self._total_length)
                    ],
                    dtype=np.uint,
                )
                + self.index_bias
            )
        offset = (record_num_frames / self.frames_to_extract - self.seg_length) / 2.0
        return (
            np.array(
                [
                    i * record_num_frames / self.frames_to_extract + offset + j
                    for i in range(self.frames_to_extract)
                    for j in range(self.seg_length)
                ],
                dtype=np.int64,
            )
            + self.index_bias
        )

    def __getitem__(self, index) -> Tuple[torch.Tensor, str]:
        frame_count = self._sequences_df.loc[index, "frame_count"]
        sequence_frame_indices = (
            self._random_sample_indices(frame_count)
            if self.random_shift
            else self._sample_indices(frame_count)
        )

        sequence_path = self._sequences_df.loc[index, "sequence"]

        # Tensor of Size (self.frames_to_extract x Channel, input_size, input_size)
        # Example: (8 * 3, 224, 224) = (24, 224, 224)
        return self.get(sequence_path, sequence_frame_indices), sequence_path

    def get(self, sequence_path: str, sequence_frame_indices: np.ndarray):
        """Extract the frames for the record, transform them as PIL.Images and transform them with
        `self.transform`"""
        vr = VideoReader(sequence_path, ctx=cpu(0))
        frames = vr.get_batch(sequence_frame_indices)

        pil_frames = [PIL.Image.fromarray(frame) for frame in frames.asnumpy()]

        process_data = self.transform(pil_frames)

        return process_data

    def __len__(self):
        return len(self._sequences_df)
