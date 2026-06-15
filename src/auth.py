import os
import sys


DEFAULT_ADMIN_USER = 'gustavo'
DEFAULT_ADMIN_PASSWORD = '123'


def get_admin_credentials() -> tuple[str, str]:
    usuario = os.getenv('ADAPTAESCOLA_ADMIN_USER') or os.getenv('ADAPTAESCOLA_ADMIN_EMAIL') or DEFAULT_ADMIN_USER
    password = os.getenv('ADAPTAESCOLA_ADMIN_PASSWORD', DEFAULT_ADMIN_PASSWORD)
    return usuario, password


def get_storage_secret() -> str:
    return os.getenv('ADAPTAESCOLA_STORAGE_SECRET', 'troque-este-segredo-em-producao')


def get_app_port() -> int:
    if len(sys.argv) > 1:
        return int(sys.argv[1])
    return int(os.getenv('ADAPTAESCOLA_PORT', '8110'))
