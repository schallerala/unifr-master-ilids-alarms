from contextlib import contextmanager
from typing import Generator, Optional

from ilids.synchronization.gpu_sync_manager import get_client


@contextmanager
def acquire_free_gpu(
    host: str, port: int, auth_key: bytes = b"16-896-375"
) -> Generator[int, None, None]:
    client = get_client(host, port, auth_key)
    client.connect()

    gpu_id: Optional[int] = None

    try:
        gpu_id = client.acquire_gpu()._getvalue()
        yield gpu_id
    finally:
        if gpu_id is not None:
            client.release_gpu(gpu_id)
