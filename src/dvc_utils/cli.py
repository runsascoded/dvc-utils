import json
import shlex
from os import listdir
from os.path import isdir, join
from typing import Tuple

import click
from click import option, argument, group
from qmdx import join_pipelines
from utz import process, err, hash_file

from dvc_utils.path import dvc_paths, dvc_cache_path


@group()
def cli():
    pass


@cli.command('diff', short_help='Diff a DVC-tracked file at two commits (or one commit vs. current worktree), optionally passing both through another command first')
@option('-c/-C', '--color/--no-color', default=None, help='Force or prevent colorized output')
@option('-r', '--refspec', help='<commit 1>..<commit 2> (compare two commits) or <commit> (compare <commit> to the worktree)')
@option('-R', '--ref', help='Shorthand for `-r <ref>^..<ref>`, i.e. inspect a specific commit (vs. its parent)')
@option('-s', '--shell-executable', help=f'Shell to use for executing commands; defaults to $SHELL')
@option('-S', '--no-shell', is_flag=True, help="Don't pass `shell=True` to Python `subprocess`es")
@option('-U', '--unified', type=int, help='Number of lines of context to show (passes through to `diff`)')
@option('-v', '--verbose', is_flag=True, help="Log intermediate commands to stderr")
@option('-w', '--ignore-whitespace', is_flag=True, help="Ignore whitespace differences (pass `-w` to `diff`)")
@option('-x', '--exec-cmd', 'exec_cmds', multiple=True, help='Command(s) to execute before diffing; alternate syntax to passing commands as positional arguments')
@argument('args', metavar='[exec_cmd...] <path>', nargs=-1)
def dvc_utils_diff(
    color: bool | None,
    refspec: str | None,
    ref: str | None,
    shell_executable: str | None,
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

    if refspec and ref:
        raise ValueError("Specify -r/--refspec xor -R/--ref")
    if ref:
        refspec = f'{ref}^..{ref}'
    elif not refspec:
        refspec = 'HEAD'

    pcs = refspec.split('..', 1)
    if len(pcs) == 1:
        before = pcs[0]
        after = None
    elif len(pcs) == 2:
        before, after = pcs
    else:
        raise ValueError(f"Invalid refspec: {refspec}")

    log = err if verbose else False
    path1 = dvc_cache_path(before, dvc_path, log=log)
    path2 = (path if after is None else dvc_cache_path(after, dvc_path, log=log))

    if isdir(path):
        dir_json1 = dir_json2 = {}
        if path1:
            with open(path1, 'r') as f:
                obj = json.load(f)
                dir_json1 = { e["relpath"]: e["md5"] for e in obj }
        if path2:
            if path2 == path and after is None:
                dir_json2 = {}
                for file in listdir(path2):
                    md5 = hash_file(join(path2, file), hash_name='md5')
                    dir_json2[file] = md5
            else:
                with open(path2, 'r') as f:
                    dir_json2 = { obj["relpath"]: obj["md5"] for obj in json.load(f) }
        for relpath in sorted(set(dir_json1) | set(dir_json2)):
            md5_1 = dir_json1.get(relpath)
            md5_2 = dir_json2.get(relpath)
            if md5_1 != md5_2:
                print(f'{relpath}: {md5_1} -> {md5_2}')
    else:
        diff_args = [
            *(['-w'] if ignore_whitespace else []),
            *(['-U', str(unified)] if unified is not None else []),
            *(['--color=always'] if color is True else ['--color=never'] if color is False else []),
        ]
        if cmds:
            cmd, *sub_cmds = cmds
            cmds1 = [ 'cat /dev/null' ] if path1 is None else [ f'{cmd} {path1 or "/dev/null"}', *sub_cmds ]
            cmds2 = [ 'cat /dev/null' ] if path2 is None else [ f'{cmd} {path2 or "/dev/null"}', *sub_cmds ]
            if not shell:
                cmds1 = [ shlex.split(cmd) for cmd in cmds1 ]
                cmds2 = [ shlex.split(cmd) for cmd in cmds2 ]

            join_pipelines(
                base_cmd=['diff', *diff_args],
                cmds1=cmds1,
                cmds2=cmds2,
                verbose=verbose,
                shell=shell,
                executable=shell_executable,
            )
        else:
            res = process.run('diff', *diff_args, path1 or '/dev/null', path2 or '/dev/null', log=log, check=False)
            exit(res.returncode)


if __name__ == '__main__':
    cli()
