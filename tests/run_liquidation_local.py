"""Isolated local browser acceptance, no production database or credentials."""
import os
from pathlib import Path
import runpy
import sys
import tempfile
import threading

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import make_server

with tempfile.TemporaryDirectory() as directory:
    os.environ.update(NAGORA_DEMO_ONLY='1',NAGORA_ORIGIN='',RENDER_EXTERNAL_URL='',RENDER='false')
    server=make_server(Path(directory)/'browser.sqlite',port=0)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    os.environ['NAGORA_TEST_URL']=server.origin
    try:
        runpy.run_path(str(Path(__file__).with_name('liquidation_browser.py')),run_name='__main__')
    finally:
        server.shutdown();server.server_close();thread.join()
