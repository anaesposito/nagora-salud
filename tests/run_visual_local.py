"""Run browser tests with a disposable database, never the real local database."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder:
    env = dict(os.environ, NAGORA_DEMO_ONLY=os.getenv('NAGORA_QA_DEMO_ONLY','1'), NAGORA_DB=str(Path(folder) / 'demo.sqlite'),
               NAGORA_PORT='8765', NAGORA_ORIGIN='http://127.0.0.1:8765',
               NAGORA_TEST_URL='http://127.0.0.1:8765', RENDER='false', RENDER_EXTERNAL_URL='')
    with open(Path(folder) / 'server.log', 'w') as log:
        process = subprocess.Popen([sys.executable, 'server.py'], cwd=ROOT, env=env, stdout=log, stderr=log)
        try:
            for attempt in range(40):
                if process.poll() is not None:
                    raise RuntimeError('Test server exited')
                try:
                    with urlopen(env['NAGORA_TEST_URL'] + '/api/config', timeout=1):
                        break
                except OSError:
                    time.sleep(.25)
            else:
                raise RuntimeError('Test server did not start')
            subprocess.run([sys.executable, os.getenv('NAGORA_QA_SCRIPT','tests/visual_smoke.py')], cwd=ROOT, env=env, check=True)
        finally:
            process.terminate()
            process.wait(timeout=10)
