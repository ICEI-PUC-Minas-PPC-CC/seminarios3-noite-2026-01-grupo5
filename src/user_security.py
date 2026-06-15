import base64
import datetime
import hashlib
import hmac
import os


HASH_ALGORITHM = 'pbkdf2_sha256'
HASH_ITERATIONS = 210_000


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def _b64decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode('ascii'))


def gerar_hash_senha(senha: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac('sha256', str(senha).encode('utf-8'), salt, HASH_ITERATIONS)
    return f'{HASH_ALGORITHM}${HASH_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}'


def verificar_hash_senha(senha: str, senha_hash: str) -> bool:
    try:
        algoritmo, iteracoes, salt_b64, digest_b64 = str(senha_hash).split('$', 3)
        if algoritmo != HASH_ALGORITHM:
            return False
        salt = _b64decode(salt_b64)
        digest_armazenado = _b64decode(digest_b64)
        digest_digitado = hashlib.pbkdf2_hmac(
            'sha256',
            str(senha).encode('utf-8'),
            salt,
            int(iteracoes),
        )
        return hmac.compare_digest(digest_digitado, digest_armazenado)
    except Exception:
        return False


def senha_confere(usuario: dict, senha: str) -> bool:
    senha_hash = usuario.get('senha_hash')
    if senha_hash:
        return verificar_hash_senha(senha, senha_hash)

    senha_legada = usuario.get('senha')
    if senha_legada is None:
        return False
    return hmac.compare_digest(str(senha_legada), str(senha))


def definir_senha(usuario: dict, senha: str) -> None:
    usuario['senha_hash'] = gerar_hash_senha(senha)
    usuario['senha_atualizada_em'] = datetime.datetime.now().strftime('%d/%m/%Y')
    usuario.pop('senha', None)


def usuario_tem_senha(usuario: dict) -> bool:
    return bool(usuario.get('senha_hash') or usuario.get('senha'))


def migrar_senha_legada(usuario: dict, senha: str) -> bool:
    if usuario.get('senha_hash') or not senha_confere(usuario, senha):
        return False

    definir_senha(usuario, senha)
    return True
