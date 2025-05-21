import json
import shlex
from os import listdir
from os.path import isdir, join
from typing import Tuple

import click
from click import option, argument, group
from dffs import join_pipelines
from utz import process, err, hash_file

from dvc_utils.path import dvc_paths, dvc_cache_path


@group()
def cli():
    pass
