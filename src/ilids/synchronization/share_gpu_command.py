import typer

from ilids.synchronization.del_file_lock import DeleteFileLock
from ilids.synchronization.gpu_sync_manager import get_server_manager

typer_app = typer.Typer()

FILE_LOCK_PATH = f"{__name__}.lock"


@typer_app.command()
def serve_gpu_sync(gpu_count: int, port: int):
    lock = DeleteFileLock(FILE_LOCK_PATH, timeout=1)

    with lock:
        server = get_server_manager(gpu_count, port).get_server()
        print(f"Starting multiprocess Manager on port {port}...")

        server.serve_forever()
