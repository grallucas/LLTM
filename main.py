import importlib
import sys
from pathlib import Path

sys.path.append("./backend")
import server

sys.path.append("./llm_core")
import llm
import learning_with_variation

sys.path.append("./srs")
import SRS

llm.LLM('') # cold start
print('started')

while True:
    app_fn = server.get_app(learning_with_variation, llm, SRS, Path.cwd().as_posix(), 8001)
    app_fn()

    opt = input('Use letters to restart [(b)ackend (l)lm (s)rs] or nothing to quit: ')

    if not opt:
        break
    if 'b' in opt:
        Path('backend/server.py').touch()
        importlib.reload(server)
        Path('llm_core/learning_with_variation.py').touch()
        importlib.reload(learning_with_variation)
    if 's' in opt:
        Path('srs/SRS.py').touch()
        importlib.reload(SRS)
    if 'l' in opt:
        Path('llm_core/llm.py').touch()
        importlib.reload(llm)
