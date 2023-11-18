import shlex
from os.path import join
from subprocess import Popen

import click
import yaml
from utz import process, singleton, err

from dvc_utils.named_pipes import named_pipes


@click.group()
def cli():
    pass


def dvc_paths(path):
    if path.endswith('.dvc'):
        dvc_path = path
        path = dvc_path[:-len('.dvc')]
    else:
        dvc_path = f'{path}.dvc'
    return path, dvc_path


def dvc_md5(git_ref, dvc_path, log=False):
    dvc_spec = process.output('git', 'show', f'{git_ref}:{dvc_path}', log=log)
    dvc_obj = yaml.safe_load(dvc_spec)
    out = singleton(dvc_obj['outs'], dedupe=False)
    md5 = out['md5']
    return md5


_dvc_cache_dir = None
def dvc_cache_dir(log=False):
    global _dvc_cache_dir
    if _dvc_cache_dir is None:
        _dvc_cache_dir = process.line('dvc', 'cache', 'dir', log=log)
    return _dvc_cache_dir


def dvc_cache_path(spec, dvc_path=None, log=False):
    if dvc_path:
        md5 = dvc_md5(spec, dvc_path, log=log)
    elif ':' in spec:
        git_ref, dvc_path = spec.split(':', 1)
        md5 = dvc_md5(git_ref, dvc_path, log=log)
    else:
        md5 = spec
    dirname = md5[:2]
    basename = md5[2:]
    return join(dvc_cache_dir(log=log), 'files', 'md5', dirname, basename)


def diff_cmds(cmd1, cmd2, **kwargs):
    """Run two commands and diff their output.

    Adapted from https://stackoverflow.com/a/28840955"""
    with named_pipes(n=2) as paths:
        someprogram = Popen(['diff'] + paths)
        processes = []
        for path, cmd in zip(paths, [ cmd1, cmd2 ]):
            with open(path, 'wb', 0) as pipe:
                processes.append(Popen(cmd, stdout=pipe, close_fds=True, **kwargs))
        for p in [someprogram] + processes:
            p.wait()


@cli.command('diff', short_help='Diff a DVC-tracked file at two commits (or one commit vs. current worktree), optionally passing both through another command first')
@click.option('-r', '--refspec', default='HEAD', help='<commit 1>..<commit 2> (compare two commits) or <commit> (compare <commit> to the worktree)')
@click.option('-S', '--no-shell', is_flag=True, help="Don't pass `shell=True` to Python `subprocess`es")
@click.option('-v', '--verbose', is_flag=True, help="Log intermediate commands to stderr")
@click.argument('args', metavar='[cmd...] <path>', nargs=-1)
def dvc_utils_diff(refspec, no_shell, verbose, args):
    """Diff a file at two commits (or one commit vs. current worktree), optionally passing both through `cmd` first

    Examples:

    dvc-utils diff -r HEAD^..HEAD wc -l foo.dvc  # Compare the number of lines (`wc -l`) in `foo` (the file referenced by `foo.dvc`) at the previous vs. current commit (`HEAD^..HEAD`).

    dvc-utils diff md5sum foo  # Diff the `md5sum` of `foo` (".dvc" extension is optional) at HEAD (last committed value) vs. the current worktree content.
    """
    if not args:
        raise click.UsageError('Must specify [cmd...] <path>')

    shell = not no_shell
    (*cmd, path) = args
    if path.endswith('.dvc'):
        dvc_path = path
        path = dvc_path[:-len('.dvc')]
    else:
        dvc_path = f'{path}.dvc'

    pcs = refspec.split('..', 1)
    if len(pcs) == 1:
        before = pcs[0]
        after = None
    else:
        before, after = pcs

    log = err if verbose else False
    before_path = dvc_cache_path(before, dvc_path, log=log)
    after_path = path if after is None else dvc_cache_path(after, dvc_path, log=log)

    if cmd:
        def args(path):
            arr = cmd + [path]
            return shlex.join(arr) if shell else arr

        shell_kwargs = dict(shell=shell) if shell else {}
        before_cmd = args(before_path)
        after_cmd = args(after_path)
        diff_cmds(before_cmd, after_cmd, **shell_kwargs)
    else:
        process.run('diff', before_path, after_path, log=log)


if __name__ == '__main__':
    cli()
