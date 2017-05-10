from fabric.contrib.files import append, exists, sed
from fabric.api import env, local, run
from fabric.operations import sudo
import random

REPO_URL = 'https://github.com/painchjy/book-example.git'

def deploy():
    site_folder = f'/home/{env.user}/sites/{env.host}'
    source_folder = site_folder + '/source'
    _create_directory_structure_if_necessary(site_folder)
    _get_latest_source(source_folder)
    _update_settings(source_folder, env.host)
    _update_virtualenv(source_folder)
    _update_static_files(source_folder)
    _update_database(source_folder)
    _config_nginx_gunicorn(source_folder, env.host)

def _create_directory_structure_if_necessary(site_folder):
    for subfolder in ('database', 'static', 'virtualenv', 'source'):
        run(f'mkdir -p {site_folder}/{subfolder}')

def _get_latest_source(source_folder):
    if exists(source_folder + '/.git'):
        run(f'cd {source_folder} && git fetch')
    else:
        run(f'git clone {REPO_URL} {source_folder}')
    current_commit = local("git log -n 1 --format=%H", capture=True)
    run(f'cd {source_folder} && git reset --hard {current_commit}')

def _update_settings(source_folder, site_name):
    settings_path = source_folder + '/superlists/settings.py'
    sed(settings_path, "DEBUG = True", "DEBUG = False")
    sed(settings_path,
        'ALLOWED_HOSTS =.+$',
        f'ALLOWED_HOSTS = ["{site_name}"]'
    )
    secret_key_file = source_folder + '/superlists/secret_key.py'
    if not exists(secret_key_file):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
        append(secret_key_file, f'SECRET_KEY = "{key}"')
    append(settings_path, '\nfrom .secret_key import SECRET_KEY')

def _update_virtualenv(source_folder):
    virtualenv_folder = source_folder + '/../virtualenv'
    if not exists(virtualenv_folder + '/bin/pip'):
        run(f'python3.6 -m venv {virtualenv_folder}')
    run(f'{virtualenv_folder}/bin/pip install -r {source_folder}/requirements.txt')

def _update_static_files(source_folder):
    run(
        f'cd {source_folder}'
        ' && ../virtualenv/bin/python manage.py collectstatic --noinput'
    )

def _update_database(source_folder):
    run(
        f'cd {source_folder}'
        ' && ../virtualenv/bin/python manage.py migrate --noinput'
    )
def _config_nginx_gunicorn(source_folder, site_name):
    if not exists(f'/etc/nginx/sites-available/{site_name}'):
        sudo(f'sed "s/SITENAME/{site_name}/g" '
            f' {source_folder}/deploy_tools/nginx.template.conf | tee'
            f' /etc/nginx/sites-available/{site_name}'
        )
    if not exists(f'/etc/nginx/sites-enabled/{site_name}'):
        sudo(f'ln -s /etc/nginx/sites-available/{site_name}'
             f' /etc/nginx/sites-enabled/{site_name}'
        )
    if not exists(f'/etc/systemd/system/gunicorn-{site_name}.service'):
        sudo(f'sed "s/SITENAME/{site_name}/g"'
            f' {source_folder}/deploy_tools/gunicorn-systemd.template.service | tee'
            f' /etc/systemd/system/gunicorn-{site_name}.service'
        )

