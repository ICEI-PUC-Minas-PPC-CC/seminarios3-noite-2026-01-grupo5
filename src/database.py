import datetime
import json
import sqlite3
from copy import deepcopy
from json import JSONDecodeError
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
DB_PATH = DATA_DIR / 'ruthsee.db'


def get_database_path() -> Path:
    return DB_PATH


def _collection_name(filename: str) -> str:
    name = Path(filename).name
    if name != filename:
        raise ValueError('Use apenas nomes de colecao simples, sem caminho.')
    return name


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute('PRAGMA journal_mode=WAL')
    connection.execute('PRAGMA foreign_keys=ON')
    connection.execute(
        '''
        CREATE TABLE IF NOT EXISTS collections (
            name TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        '''
    )
    return connection


def _read_json_seed(filename: str, default_data: Any) -> Any:
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return deepcopy(default_data)

    try:
        with filepath.open('r', encoding='utf-8') as file:
            return json.load(file)
    except (JSONDecodeError, OSError):
        return deepcopy(default_data)


def _write_collection(connection: sqlite3.Connection, name: str, data: Any) -> None:
    payload = json.dumps(data, ensure_ascii=False)
    updated_at = datetime.datetime.now().isoformat(timespec='seconds')
    connection.execute(
        '''
        INSERT OR REPLACE INTO collections (name, payload, updated_at)
        VALUES (?, ?, ?)
        ''',
        (name, payload, updated_at),
    )


def load_data(filename: str, default_data: Any) -> Any:
    """Carrega uma colecao do SQLite e migra o JSON antigo quando necessario."""
    name = _collection_name(filename)

    connection = _connect()
    try:
        row = connection.execute(
            'SELECT payload FROM collections WHERE name = ?',
            (name,),
        ).fetchone()

        if row:
            try:
                return json.loads(row[0])
            except JSONDecodeError:
                return deepcopy(default_data)

        data = _read_json_seed(name, default_data)
        _write_collection(connection, name, data)
        connection.commit()
        return deepcopy(data)
    finally:
        connection.close()


def save_data(filename: str, data: Any) -> None:
    """Salva uma colecao no SQLite em transacao."""
    name = _collection_name(filename)

    connection = _connect()
    try:
        _write_collection(connection, name, data)
        connection.commit()
    finally:
        connection.close()
