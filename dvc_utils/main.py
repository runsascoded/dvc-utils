from functools import cache
from os import environ as env, getcwd
from os.path import join, relpath
import shlex
from subprocess import Popen, PIPE
from typing import Optional, Tuple

from click import option, argument, group
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
    dvc_spec = process.output('git', 'show', f'{git_ref}:{dir_path}{dvc_path}', log=err if log else None)
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


def diff_cmds(
    cmds1: list[str],
    cmds2: list[str],
    verbose: bool = False,
    color: bool = False,
    unified: int | None = None,
    ignore_whitespace: bool = False,
    **kwargs,
):
    """Run two sequences of piped commands and diff their output.

    Args:
        cmds1: First sequence of commands to pipe together
        cmds2: Second sequence of commands to pipe together
        verbose: Whether to print commands being executed
        color: Whether to show colored diff output
        unified: Number of unified context lines, or None
        ignore_whitespace: Whether to ignore whitespace changes
        **kwargs: Additional arguments passed to subprocess.Popen

    Each command sequence will be piped together before being compared.
    For example, if cmds1 = ['cat foo.txt', 'sort'], the function will
    execute 'cat foo.txt | sort' before comparing with cmds2's output.

    Adapted from https://stackoverflow.com/a/28840955"""
    with named_pipes(n=2) as pipes:
        (pipe1, pipe2) = pipes
        diff_cmd = [
            'diff',
            *(['-w'] if ignore_whitespace else []),
            *(['-U', str(unified)] if unified is not None else []),
            *(['--color=always'] if color else []),
            pipe1,
            pipe2,
        ]
        diff = Popen(diff_cmd)
        processes = []

        for pipe, cmds in ((pipe1, cmds1), (pipe2, cmds2)):
            if verbose:
                err(f"Running pipeline: {' | '.join(cmds)}")

            # Create the pipeline of processes
            prev_process = None
            for i, cmd in enumerate(cmds):
                is_last = i + 1 == len(cmds)

                # For the first process, take input from the original source
                stdin = None if prev_process is None else prev_process.stdout

                # For the last process, output to the named pipe
                if is_last:
                    with open(pipe, 'wb', 0) as pipe_fd:
                        proc = Popen(
                            cmd,
                            stdin=stdin,
                            stdout=pipe_fd,
                            close_fds=True,
                            **kwargs
                        )
                # For intermediate processes, output to a pipe
                else:
                    proc = Popen(
                        cmd,
                        stdin=stdin,
                        stdout=PIPE,
                        close_fds=True,
                        **kwargs
                    )

                if prev_process is not None:
                    prev_process.stdout.close()

                processes.append(proc)
                prev_process = proc

        for p in [diff] + processes:
            p.wait()


@cli.command('diff', short_help='Diff a DVC-tracked file at two commits (or one commit vs. current worktree), optionally passing both through another command first')
@option('-c', '--color', is_flag=True, help='Colorize the output')
@option('-r', '--refspec', default='HEAD', help='<commit 1>..<commit 2> (compare two commits) or <commit> (compare <commit> to the worktree)')
@option('-S', '--no-shell', is_flag=True, help="Don't pass `shell=True` to Python `subprocess`es")
@option('-U', '--unified', type=int, help='Number of lines of context to show (passes through to `diff`)')
@option('-v', '--verbose', is_flag=True, help="Log intermediate commands to stderr")
@option('-w', '--ignore-whitespace', is_flag=True, help="Ignore whitespace differences (pass `-w` to `diff`)")
@option('-x', '--exec-cmd', 'exec_cmds', multiple=True, help='Command(s) to execute before diffing; alternate syntax to passing commands as positional arguments')
@argument('args', metavar='[exec_cmd...] <path>', nargs=-1)
def dvc_utils_diff(
    color: bool,
    refspec: str | None,
    no_shell: bool,
    unified: int | None,
    verbose: bool,
    ignore_whitespace: bool,
    exec_cmds: Tuple[str, ...],
    args: Tuple[str, ...],
):
    """Diff a file at two commits (or one commit vs. current worktree), optionally passing both through `cmd` first

    Examples:

    dvc-utils diff -r HEAD^..HEAD wc -l foo.dvc  # Compare the number of lines (`wc -l`) in `foo` (the file referenced by `foo.dvc`) at the previous vs. current commit (`HEAD^..HEAD`).

    dvc-utils diff md5sum foo  # Diff the `md5sum` of `foo` (".dvc" extension is optional) at HEAD (last committed value) vs. the current worktree content.
    """
    if not args:
        raise click.UsageError('Must specify [cmd...] <path>')

    shell = not no_shell
    *cmds, path = args
    cmds = list(exec_cmds) + cmds

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

    if cmds:
        cmd, *sub_cmds = cmds
        if not shell:
            sub_cmds = [ shlex.split(c) for c in sub_cmds ]
            before_cmds = [
                shlex.split(f'{cmd} {before_path}'),
                *sub_cmds,
            ]
            after_cmds = [
                shlex.split(f'{cmd} {after_path}'),
                *sub_cmds,
            ]
            shell_kwargs = {}
        else:
            before_cmds = [ f'{cmd} {before_path}', *sub_cmds ]
            after_cmds = [ f'{cmd} {after_path}', *sub_cmds ]
            shell_kwargs = dict(shell=shell)

        diff_cmds(
            before_cmds,
            after_cmds,
            verbose=verbose,
            color=color,
            unified=unified,
            ignore_whitespace=ignore_whitespace,
            **shell_kwargs,
        )
    else:
        process.run('diff', before_path, after_path, log=log)


if __name__ == '__main__':
    cli()
