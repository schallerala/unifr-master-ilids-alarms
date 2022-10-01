import contextlib
from typing import Generator, Optional

import torch

from ilids.synchronization.acquire_gpu_client import acquire_free_gpu
from ilids.utils.extended_enums import ExtendedEnum


class DeviceType(str, ExtendedEnum):
    cpu = "cpu"
    cuda = "cuda"


@contextlib.contextmanager
def alternate_device(
    target_device: DeviceType,
    distributed: bool,
    sync_server_host: Optional[str] = None,
    sync_server_port: Optional[int] = None,
) -> Generator[torch.device, None, None]:
    assert not (distributed and target_device == DeviceType.cpu)

    if target_device == DeviceType.cpu:
        yield torch.device("cpu")

    else:
        if distributed:
            with acquire_free_gpu(sync_server_host, sync_server_port) as gpu_id:
                device = torch.device("cuda", gpu_id)
                yield device

        else:
            assert torch.cuda.is_available()
            yield torch.device("cuda")
