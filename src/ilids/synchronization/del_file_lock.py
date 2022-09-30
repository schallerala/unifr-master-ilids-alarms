from pathlib import Path

from filelock import FileLock


class DeleteFileLock(FileLock):
    def _acquire(self) -> None:
        super()._acquire()

    def _release(self) -> None:
        super()._release()

        Path(self.lock_file).unlink(missing_ok=True)
