import importlib
import sys
from pathlib import Path

sys.path.append("./backend")
import server

sys.path.append("./llm_core")
import llm

llm.LLM('') # cold start

while True:
    app_fn = server.get_app(llm, Path.cwd().as_posix(), 8001)
    app_fn()

    opt = input('Use letters to restart [(s)erver (l)lm] or nothing to quit: ')

    if not opt:
        break
    if 's' in opt:
        Path('backend/server.py').touch()
        importlib.reload(server)
    if 'l' in opt:
        Path('llm_core/llm.py').touch()
        importlib.reload(llm)
