from typing import List, Optional

import typer

from ilids.synchronization.del_file_lock import DeleteFileLock
from ilids.synchronization.gpu_sync_manager import get_server_manager

typer_app = typer.Typer()

FILE_LOCK_PATH = f"{__name__}.lock"


@typer_app.command()
def serve_gpu_sync(
    port: int = typer.Option(..., "-p", "--port"),
    gpu_count: Optional[int] = typer.Option(None, "--count"),
    available_gpus: Optional[List[int]] = typer.Option(None, "--available"),
):
    # instead of empty list, set to None, which reverts a bit typer's logic
    available_gpus = None if len(available_gpus) == 0 else set(available_gpus)

    assert (
        gpu_count is None or available_gpus is None
    ), "Specify at least one of the options: --count or --available"
    assert available_gpus is None or len(available_gpus) > 0

    free_gpus = available_gpus or set(range(gpu_count))

    lock = DeleteFileLock(FILE_LOCK_PATH, timeout=1)

    with lock:
        server = get_server_manager(free_gpus, port).get_server()
        print(f"Starting multiprocess Manager on port {port}...")

        server.serve_forever()
