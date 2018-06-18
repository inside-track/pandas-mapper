import os

from invoke import task

@task
def package(ctx):
    '''
    Package distribution to upload to PyPI
    '''
    ctx.run('rm -rf dist')
    ctx.run('python setup.py sdist')

@task
def package_deploy(ctx):
    '''
    Deploy package to PyPI
    '''
    ctx.run('twine upload dist/*')

@task
def compile_requirements(ctx):
    '''
    Compile Python requirements without upgrading.
    Docker images need to be rebuilt after running this (inv build).
    '''
    ctx.run('docker-compose run app inv pip-compile')

@task
def upgrade_requirements(ctx):
    '''
    Compile Python requirements with upgrading.
    Docker images need to be rebuilt after running this (inv build).
    '''
    ctx.run('docker-compose run app inv pip-compile-upgrade')

@task
def build(ctx):
    'Build docker images'
    ctx.run('docker-compose build')

@task(help={
    'host-port': 'Used to override the default flask port on the host (default: 8888)'
})
def up(ctx, jupyter_port=8888):
    'Start up development environment'

    os.environ['HOST_JUPYTER_PORT'] = str(jupyter_port)
    ctx.run('docker-compose up -d')

@task
def down(ctx):
    'Shut down development environment'
    ctx.run('docker-compose down')

@task(down, up)
def restart(ctx):
    'Restart development environment'

@task(help={'pytest': "Arguments to pass to pytest running in the container."})
def test(ctx, pytest=''):
    'Runs the test suite.  User can specifiy pytest options to run specific tests.'
    ctx.run('docker-compose run app pytest {}'.format(pytest))

@task
def logs(ctx):
    'Follow docker logs'
    ctx.run('docker-compose logs -f')

@task
def ps(ctx):
    'View environment containers'
    ctx.run('docker-compose ps')

@task
def shell(ctx):
    'Start a shell running in the app container'
    ctx.run('docker-compose run --rm app /bin/bash')

@task
def pip_compile(ctx):
    'Compile pip resources.  This should only be run in the container.'
    ctx.run('pip-compile requirements.in')

@task
def pip_compile_upgrade(ctx):
    'Upgrate pip resources.  This should only be run in the container.'
    ctx.run('pip-compile -U requirements.in')
