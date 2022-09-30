from multiprocessing.managers import BaseManager


class SharedSetManager(BaseManager):
    def acquire_gpu(self) -> int:
        pass

    def release_gpu(self, gpu_id: int):
        pass


def get_server_manager(
    gpu_count: int, port: int, auth_key: bytes = b"16-896-375"
) -> SharedSetManager:
    free_gpus = set(range(gpu_count))

    def _acquire_gpu() -> int:
        free_gpu = free_gpus.pop()
        print(f"Giving free GPU {free_gpu}")
        return free_gpu

    def _release_gpu(gpu_id: int):
        free_gpus.add(gpu_id)
        print(f"GPU {gpu_id} is free")

    SharedSetManager.register("acquire_gpu", callable=_acquire_gpu)
    SharedSetManager.register("release_gpu", callable=_release_gpu)

    manager = SharedSetManager(address=("", port), authkey=auth_key)

    return manager


def get_client(
    host: str, port: int, auth_key: bytes = b"16-896-375"
) -> SharedSetManager:
    SharedSetManager.register("acquire_gpu")
    SharedSetManager.register("release_gpu")

    manager = SharedSetManager(address=(host, port), authkey=auth_key)

    return manager
