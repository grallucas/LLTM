import importlib
import sys
from pathlib import Path

sys.path.append("./backend")
import server

sys.path.append("./llm_core")
import llm
import learning_llm

sys.path.append("./srs")
import SRS

llm.LLM('') # cold start
print('started')

while True:
    app_fn = server.get_app(learning_llm, llm, SRS, Path.cwd().as_posix(), 8001)
    app_fn()

    opt = input('Use letters to restart [(b)ackend (l)lm (s)rs] or nothing to quit: ')

    if not opt:
        break
    if 'b' in opt:
        Path('backend/server.py').touch()
        importlib.reload(server)
        Path('llm_core/learning_llm.py').touch()
        importlib.reload(learning_llm)
    if 's' in opt:
        Path('srs/SRS.py').touch()
        importlib.reload(SRS)
    if 'l' in opt:
        Path('llm_core/llm.py').touch()
        importlib.reload(llm)
