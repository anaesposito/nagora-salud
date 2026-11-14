"""Consistent SQLite backup and offline restore to a NEW destination only."""
import argparse
import os
import sqlite3
from contextlib import closing
from pathlib import Path


def copy_database(source, destination, restore=False):
    source, destination = Path(source).resolve(strict=True), Path(destination).absolute()
    if source == destination:
        raise ValueError('El destino debe ser un archivo nuevo.')
    # Exclusive creation protects existing databases, including symlinks.
    fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as src:
            with closing(sqlite3.connect(destination)) as dst:
                src.backup(dst)
                if dst.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                    raise ValueError('La copia no superó la verificación de integridad.')
                if dst.execute('PRAGMA foreign_key_check').fetchall():
                    raise ValueError('La copia contiene relaciones inválidas.')
                if restore:
                    # Old sessions and recovery codes must not become valid again.
                    with dst:
                        dst.execute('DELETE FROM session')
                        dst.execute('DELETE FROM recovery')
        return destination
    except Exception:
        destination.unlink(missing_ok=True)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['backup', 'restore'])
    parser.add_argument('source')
    parser.add_argument('destination', help='Archivo nuevo; nunca se sobrescribe una base existente')
    args = parser.parse_args()
    copy_database(args.source, args.destination, restore=args.operation == 'restore')
    print('Copia verificada correctamente.')
