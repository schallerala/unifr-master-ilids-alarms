"""From: https://stackoverflow.com/a/61027781/3771148"""

import joblib
from tqdm.auto import tqdm


class ProgressParallel(joblib.Parallel):
    def __init__(
        self,
        n_jobs=None,
        backend=None,
        verbose=0,
        timeout=None,
        pre_dispatch="2 * n_jobs",
        batch_size="auto",
        temp_folder=None,
        max_nbytes="1M",
        mmap_mode="r",
        prefer=None,
        require=None,
        **tqdm_kwargs
    ):
        super().__init__(
            n_jobs,
            backend,
            verbose,
            timeout,
            pre_dispatch,
            batch_size,
            temp_folder,
            max_nbytes,
            mmap_mode,
            prefer,
            require,
        )
        self._tqdm_kwargs = tqdm_kwargs

    def __call__(self, *args, **kwargs):
        with tqdm(**self._tqdm_kwargs) as self._pbar:
            self._pbar.refresh()
            return joblib.Parallel.__call__(self, *args, **kwargs)

    def print_progress(self):
        self._pbar.total = self.n_dispatched_tasks
        self._pbar.n = self.n_completed_tasks
        self._pbar.refresh()
