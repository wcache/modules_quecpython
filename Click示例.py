import os
import click
from pathlib import Path
from git.repo import Repo
from git.exc import GitError


# --------------common utils------------------

class Repository(click.ParamType):
    name = "repository"

    def convert(self, value, param, ctx):
        try:
            repo = Repo(value)
        except GitError as e:
            self.fail(f"{value!r} is not a valid repo. origin error: {type(e), str(e)}", param, ctx)
            return
        return repo


# --------------command parts------------------
CONTEXT_SETTINGS = dict(
    default_map={'runserver': {'port': 5000}}
)


class _Repo(object):
    def __init__(self, home=None, debug=False):
        self.home = os.path.abspath(home or '.')
        self.debug = debug


# @click.group(context_settings=CONTEXT_SETTINGS)
@click.group()
@click.option('--repo-home', envvar='REPO_HOME', default='.repo')
@click.option('--debug', is_flag=True, default=False, show_default=True,
              envvar='REPO_DEBUG')
@click.pass_context
def cli(ctx, repo_home, debug):
    """A simple command line tool."""
    ctx.obj = _Repo(repo_home, debug)


@cli.command('runserver')
@click.option('--port', default=8000)
@click.pass_context
def _cmd_runserver(ctx, port):
    print(port)
    print('obj: ', ctx.obj.__dict__)
    print(ctx.__dict__)


@cli.command('import')
@click.option('--url', type=click.STRING, multiple=True)
@click.option('--yes', type=click.BOOL, default='True', show_default=True)
@click.option('--file', type=click.File(mode='r', encoding='utf8', lazy=True))
@click.option('--path', type=click.Path(exists=False, resolve_path=True, path_type=Path))
@click.option('--choice', type=click.Choice(['True', 'False'], case_sensitive=True), show_default=True)
@click.option('--repo', type=Repository(), multiple=True)
@click.option('--flag', is_flag=True, show_default=True, default=False, flag_value='FLAG_VALUE')
@click.option('--pos', nargs=2, type=click.INT)
@click.option('--account', prompt='your account', prompt_required=False, default=lambda: os.environ.get('USER', 'admin'))
@click.option('--password', prompt='your password', hide_input=True, confirmation_prompt=True)
def _cmd_import(url, yes, file, path, choice, repo, flag, pos, account, password):
    # print(url, type(url))
    # print(yes, type(yes))
    # print(file, type(file))
    # print(path, type(path))
    # print('is exists: ', path.exists())
    # print('choice: ', choice)
    # print('repo: ', repo, type(repo))
    # print('flag: ', flag, type(flag))
    # print('pos： ', pos)
    print('account: ', account)
    print('password: ', password)
    click.secho('hello world!')


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@cli.command()
# @click.option('--yes', is_flag=True, callback=abort_if_false,
#               expose_value=False,
#               prompt='Are you sure you want to drop the db?')
@click.confirmation_option(prompt='Are you sure you want to drop the db?')
@click.option('--db', envvar=['DB1', 'DB2'])
@click.option('--path', envvar='PATH', multiple=True, type=click.Path())
def dropdb(db, path):
    # print('db: ', db, type(db))
    # print('path: ', path, type(path))
    click.confirm('do you want to continue?!', abort=True)
    click.echo('Dropped all tables!')


@cli.command()
@click.argument('src', nargs=-1, required=True)
@click.argument('dst', nargs=1, required=True)
@click.option('--force', is_flag=True)
def copy(src, force, dst):
    """Move file SRC to DST."""
    print(force, src, dst)
    for fn in src:
        click.echo(f"move {fn} to folder {dst}")


@cli.command('test')
def _cmd_test():
    click.secho('Hello World!', fg='green')
    click.secho('Some more text', bg='blue', fg='red')
    click.secho('ATTENTION', blink=True, bold=True)


@cli.command('launch')
def _cmd_launch():
    click.launch('https://www.baidu.com')


if __name__ == '__main__':
    cli()
