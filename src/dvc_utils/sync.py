from click import option

from dvc_utils.cli import cli
from git import Repo


@cli.command('pull-x', short_help='Sync DVC cache files from an S3 remote')
@option('-n', '--dry-run', is_flag=True, help='Print files that would be synced, don\'t actually perform sync')
@option('-p', '--path', 'paths', multiple=True, help='Path globs to sync')
@option('-r', '--ref', 'refs', multiple=True, help='Git refs to sync DVC files from')
def pull_x(dry_run, paths, refs):
    repo = Repo()

