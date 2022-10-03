import contextlib


@contextlib.contextmanager
def notify_context(enable: bool = True) -> None:
    if not enable:
        yield  # skip notification
        return

    import mlnotify

    mlnotify.start()

    yield  # noop

    mlnotify.end()
