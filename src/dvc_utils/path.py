from __future__ import annotations

import json
from functools import cache
from os import environ as env, getcwd
from os.path import join, relpath, dirname, basename, sep
from subprocess import DEVNULL
from typing import Tuple

import yaml
from utz import process, err, singleton


def dvc_paths(path: str) -> Tuple[str, str]:
    if path.endswith(sep):
        path = path[:-len(sep)]
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


def dvc_md5(
    git_ref: str,
    dvc_path: str,
    log: bool = False,
) -> str | None:
    dir_path = get_dir_path()
    dir_path = '' if dir_path == '.' else f'{dir_path}{sep}'
    dvc_path = f"{dir_path}{dvc_path}"
    dvc_spec = process.output('git', 'show', f'{git_ref}:{dvc_path}', log=err if log else None, err_ok=True, stderr=DEVNULL)
    if dvc_spec is None:
        cur_dir = dirname(dvc_path)
        relpath = basename(dvc_path)
        if relpath.endswith(".dvc"):
            relpath = relpath[:-len(".dvc")]
        while cur_dir and cur_dir != '.':
            dir_cache_path = dvc_cache_path(ref=git_ref, dvc_path=f"{cur_dir}.dvc", log=log)
            if dir_cache_path:
                with open(dir_cache_path, 'r') as f:
                    dir_entries = json.load(f)
                md5s = [ e["md5"] for e in dir_entries if e["relpath"] == relpath ]
                if len(md5s) == 1:
                    return md5s[0]
                else:
                    raise RuntimeError(f"{relpath=} not found in DVC-tracked dir {cur_dir}")
            relpath = join(basename(cur_dir), relpath)
            cur_dir = dirname(cur_dir)
        return None
    dvc_obj = yaml.safe_load(dvc_spec)
    out = singleton(dvc_obj['outs'], dedupe=False)
    md5 = out['md5']
    return md5


def dvc_path(
    ref: str,
    dvc_path: str | None = None,
    log: bool = False,
) -> str | None:
    if dvc_path and not dvc_path.endswith('.dvc'):
        dvc_path += '.dvc'

    if dvc_path:
        md5 = dvc_md5(ref, dvc_path, log=log)
    elif ':' in ref:
        git_ref, dvc_path = ref.split(':', 1)
        md5 = dvc_md5(git_ref, dvc_path, log=log)
    else:
        md5 = ref

    if md5 is None:
        return None
    else:
        dirname = md5[:2]
        basename = md5[2:]
        return join(dvc_cache_dir(log=log), 'files', 'md5', dirname, basename)


dvc_cache_path = dvc_path
