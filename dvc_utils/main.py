from functools import cache
from os import environ as env, getcwd

from typing import Optional, Tuple

import shlex
from os.path import join, relpath

from click import option, argument, group
from subprocess import Popen

import click
import yaml
from utz import process, singleton, err

from dvc_utils.named_pipes import named_pipes


@group()
def cli():
    pass


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
    dvc_spec = process.output('git', 'show', f'{git_ref}:{dir_path}{dvc_path}', log=log)
    dvc_obj = yaml.safe_load(dvc_spec)
    out = singleton(dvc_obj['outs'], dedupe=False)
    md5 = out['md5']
    return md5


def dvc_cache_path(ref: str, dvc_path: Optional[str] = None, log: bool = False) -> str:
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


def diff_cmds(cmd1: str, cmd2: str, verbose: bool = False, **kwargs):
    """Run two commands and diff their output.

    Adapted from https://stackoverflow.com/a/28840955"""
    with named_pipes(n=2) as pipes:
        (pipe1, pipe2) = pipes
        diff = Popen(['diff'] + pipes)
        processes = []
        for path, cmd in ((pipe1, cmd1), (pipe2, cmd2)):
            with open(path, 'wb', 0) as pipe:
                if verbose:
                    err(f"Running: {cmd}")
                processes.append(Popen(cmd, stdout=pipe, close_fds=True, **kwargs))
        for p in [diff] + processes:
            p.wait()


@cli.command('diff', short_help='Diff a DVC-tracked file at two commits (or one commit vs. current worktree), optionally passing both through another command first')
@option('-r', '--refspec', default='HEAD', help='<commit 1>..<commit 2> (compare two commits) or <commit> (compare <commit> to the worktree)')
@option('-S', '--no-shell', is_flag=True, help="Don't pass `shell=True` to Python `subprocess`es")
@option('-v', '--verbose', is_flag=True, help="Log intermediate commands to stderr")
@argument('args', metavar='[cmd...] <path>', nargs=-1)
def dvc_utils_diff(refspec, no_shell, verbose, args):
    """Diff a file at two commits (or one commit vs. current worktree), optionally passing both through `cmd` first

    Examples:

    dvc-utils diff -r HEAD^..HEAD wc -l foo.dvc  # Compare the number of lines (`wc -l`) in `foo` (the file referenced by `foo.dvc`) at the previous vs. current commit (`HEAD^..HEAD`).

    dvc-utils diff md5sum foo  # Diff the `md5sum` of `foo` (".dvc" extension is optional) at HEAD (last committed value) vs. the current worktree content.
    """
    if not args:
        raise click.UsageError('Must specify [cmd...] <path>')

    shell = not no_shell
    if len(args) == 2:
        cmd, path = args
        cmd = shlex.split(cmd)
    elif len(args) == 1:
        cmd = None
        path, = args
    else:
        raise click.UsageError('Maximum 2 positional args: [cmd] <path>')

    path, dvc_path = dvc_paths(path)

    pcs = refspec.split('..', 1)
    if len(pcs) == 1:
        before = pcs[0]
        after = None
    elif len(pcs) == 2:
        before, after = pcs
    else:
        raise ValueError(f"Invalid refspec: {refspec}")

    log = err if verbose else False
    before_path = dvc_cache_path(before, dvc_path, log=log)
    after_path = path if after is None else dvc_cache_path(after, dvc_path, log=log)

    if cmd:
        def args(path: str):
            arr = cmd + [path]
            return shlex.join(arr) if shell else arr

        shell_kwargs = dict(shell=shell) if shell else {}
        before_cmd = args(before_path)
        after_cmd = args(after_path)
        diff_cmds(before_cmd, after_cmd, verbose=verbose, **shell_kwargs)
    else:
        process.run('diff', before_path, after_path, log=log)


if __name__ == '__main__':
    cli()
