from fabric.api import run
from fabric.context_managers import settings

def _get_manage_dot_py(host):
    return f'~/sites/{host}/virtualenv/bin/python ~/sites/{host}/source/manage.py'

def reset_database(host):
    manage_dot_py = _get_manage_dot_py(host)
    with settings(host_string=f'painchjy@{host}', port=27627):
        run(f'{manage_dot_py} flush --noinput')
        run(f'{manage_dot_py} loaddata ~/sites/{host}/source/fixtures/users.json')
        
def create_session_on_server(host, email):
    manage_dot_py = _get_manage_dot_py(host)
    with settings(host_string=f'painchjy@{host}', port=27627):
        session_key = run(f'{manage_dot_py} create_session {email}')
        return session_key.strip()

