from functools import cache
from os import environ as env, getcwd
from os.path import join, relpath
from typing import Optional, Tuple

import yaml
from utz import process, err, singleton


def dvc_paths(path: str) -> Tuple[str, str]:
    if path.endswith('.dvc'):
        dvc_path = path
        path = dvc_path[:-len('.dvc')]
    else:
        dvc_path = f'{path}.dvc'
    return path, dvc_path


@cache
def get_git_root() -> str:
    return process.line('git', 'rev-parse', '--show-toplevel', log=False)


@cache
def get_dir_path() -> str:
    return relpath(getcwd(), get_git_root())


@cache
def dvc_cache_dir(log: bool = False) -> str:
    dvc_cache_relpath = env.get('DVC_UTILS_CACHE_DIR')
    if dvc_cache_relpath:
        return join(get_git_root(), dvc_cache_relpath)
    else:
        return process.line('dvc', 'cache', 'dir', log=log)


def dvc_md5(git_ref: str, dvc_path: str, log: bool = False) -> str:
    dir_path = get_dir_path()
    dir_path = '' if dir_path == '.' else f'{dir_path}/'
    dvc_spec = process.output('git', 'show', f'{git_ref}:{dir_path}{dvc_path}', log=err if log else None)
    dvc_obj = yaml.safe_load(dvc_spec)
    out = singleton(dvc_obj['outs'], dedupe=False)
    md5 = out['md5']
    return md5


def dvc_path(ref: str, dvc_path: Optional[str] = None, log: bool = False) -> str:
    if dvc_path and not dvc_path.endswith('.dvc'):
        dvc_path += '.dvc'
    if dvc_path:
        md5 = dvc_md5(ref, dvc_path, log=log)
    elif ':' in ref:
        git_ref, dvc_path = ref.split(':', 1)
        md5 = dvc_md5(git_ref, dvc_path, log=log)
    else:
        md5 = ref
    dirname = md5[:2]
    basename = md5[2:]
    return join(dvc_cache_dir(log=log), 'files', 'md5', dirname, basename)
