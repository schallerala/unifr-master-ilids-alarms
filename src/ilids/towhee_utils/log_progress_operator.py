import tqdm
from towhee import register
from towhee.operator import PyOperator


@register(name="ilids/log_progress")
class LogProgress(PyOperator):
    def __init__(self, progress: tqdm.tqdm):
        super().__init__()
        self.progress = progress

    def __call__(self, *args, **kwargs):
        self.progress.update()

        return args[0]
