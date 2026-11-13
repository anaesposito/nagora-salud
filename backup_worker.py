"""Hourly local backup worker. Production requires a protected external volume."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import time
from uuid import uuid4

from backup import copy_database

NAME = re.compile(r'^nagora-\d{8}T\d{6}Z-[0-9a-f]{32}\.sqlite$')
INTERVAL = 3600
RETENTION = 30 * 86400


def run_once(source, directory, now=None):
    now = time.time() if now is None else now
    source = Path(source).resolve(strict=True)
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = datetime.fromtimestamp(now, timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target = directory / f'nagora-{stamp}-{uuid4().hex}.sqlite'
    copy_database(source, target)
    # Rotate only after a new verified copy succeeds. Never traverse directories,
    # follow symlinks, touch the source, or remove unrelated files.
    for candidate in directory.iterdir():
        if candidate == target or candidate.is_symlink() or not candidate.is_file():
            continue
        if candidate.resolve() == source or not NAME.fullmatch(candidate.name):
            continue
        if candidate.stat().st_mtime < now - RETENTION:
            candidate.unlink()
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('directory')
    parser.add_argument('--loop', action='store_true', help='Repetir cada hora; sin esta opción ejecuta una vez')
    args = parser.parse_args()
    os.umask(0o077)
    while True:
        started = time.monotonic()
        try:
            run_once(args.source, args.directory)
        except Exception as error:
            # No paths, SQL, account data or secrets in worker logs.
            print(f'backup_failed {type(error).__name__}', flush=True)
            raise SystemExit(1)
        print('backup_verified', flush=True)
        if not args.loop:
            break
        time.sleep(max(0, INTERVAL - (time.monotonic() - started)))
