from fabric.api import env, run, local, cd
from config import app_config


conf = dict()
conf['code_dir'] = None


def production():
    env.hosts = [app_config.get('deploy.production.host')]
    env.key_filename = app_config.get('deploy.production.key_file')
    conf['code_dir'] = app_config.get('deploy.production.target_dir')


def deploy():
    with cd(conf['code_dir']):
        run('git fetch')
        run('git checkout origin/master')


def restart():
    run('sudo service neutral_su_www restart')


def db_upgrade():
    with cd(conf['code_dir']):
        run('alembic upgrade head')
