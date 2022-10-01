from unittest.mock import patch

import pytest
import torch

from ilids.synchronization.alternate_device import DeviceType, alternate_device


def test_alternate_device__not_distributed_with_cpu():
    with pytest.raises(AssertionError):
        with alternate_device(DeviceType.cpu, distributed=True):
            pytest.fail("Shouldn't be able to distributed on cpu")


def test_alternate_device__not_distributed_gpu_with_available_cuda():
    with patch.object(torch.cuda, "is_available", return_value=True):
        with alternate_device(DeviceType.cuda, distributed=False) as device:
            assert device == torch.device("cuda")


def test_alternate_device__not_distributed_gpu_without_available_cuda():
    with pytest.raises(AssertionError):
        with patch.object(torch.cuda, "is_available", return_value=False):
            with alternate_device(DeviceType.cuda, distributed=False):
                pytest.fail("GPU shouldn't be available and should early fail")
