import os
import shutil
import tempfile
from contextlib import contextmanager


@contextmanager
def named_pipes(n: int = 1):
    """Yield a list of paths to named pipes that are created and destroyed

    From https://stackoverflow.com/a/28840955"""
    dirname = tempfile.mkdtemp()
    try:
        paths = [os.path.join(dirname, 'named_pipe' + str(i)) for i in range(n)]
        for path in paths:
            os.mkfifo(path)
        yield paths
    finally:
        shutil.rmtree(dirname)
