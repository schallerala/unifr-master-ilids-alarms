from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import numpy as np
from hamcrest import *
import torch.nn
from decord import VideoReader
from torch.utils.data import DataLoader

from ilids.models.actionclip.datasets import ActionDataset


@pytest.mark.handcrafted_files(("actionclip_sequences.csv", "input_sequences"))
@pytest.mark.parametrize("frames_to_extract", [8, 16, 32])
def test_ActionDataset_frame_extraction_inbound_frame_count(input_sequences: Path, frames_to_extract: int):
    input_sequences_df = pd.read_csv(input_sequences).set_index("sequence")

    ilids_dataset = ActionDataset(
        input_sequences,
        frames_to_extract=frames_to_extract,
        transform=torch.nn.Identity(),
    )
    ilids_loader = DataLoader(
        ilids_dataset,
        batch_size=64,
        shuffle=False,
        pin_memory=True,
    )

    with patch.object(VideoReader, 'get_batch') as vr_get_batch_mocked:
        # sanity check
        for i, (_frames, paths) in enumerate(ilids_loader):
            # _frames is going to be an empty array, as `get_batch` method has been mocked

            # assert frame selection
            batch_start = i * 64
            batch_end = batch_start + len(paths)
            for ii, (call_index, call_get_batch_argument) in enumerate(zip(range(batch_start, batch_end), vr_get_batch_mocked.call_args_list[batch_start:batch_end])):
                sequence_frame_indices = np.array(call_get_batch_argument[0][0])

                assert_that(len(sequence_frame_indices), is_(frames_to_extract))

                path = paths[ii]
                sequence_frame_count = input_sequences_df.loc[path, "frame_count"]

                assert_that(sequence_frame_indices.max(initial=-1), is_(less_than(sequence_frame_count)))
