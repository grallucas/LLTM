import sys

sys.path.append("./backend")
sys.path.append("./llm_core")
sys.path.append("./srs")
sys.path.append("./tts")
sys.path.append("./img_core")

import server
import llm
import learning_with_variation
import SRS
import tts
import image_gen
import dictionary

from pathlib import Path
import importlib

llm.LLM() # cold start global llm instance

while True:
    server.app_fn(8001, Path.cwd().as_posix())

    opt = input('Use letters to restart [(l)lm (i)mg (o)ther] or nothing to only restart backend. x to quit: ')

    # ORDER MATTERS: backend depends on these parts, so the parts are reloaded first.
    # NOTE: the parts cannot depend on each other, with some exceptions (e.g., they can all depend on llm)
    if 'x' in opt:
        break
    if 'l' in opt:
        Path('llm_core/llm.py').touch()
        importlib.reload(llm)
    if 'i' in opt:
        Path('./img_core/image_gen.py').touch()
        importlib.reload(image_gen)
    if 'o' in opt:
        Path('./tts/tts.py').touch()
        importlib.reload(tts)

        Path('srs/SRS.py').touch()
        importlib.reload(SRS)

        Path('llm_core/learning_with_variation.py').touch()
        importlib.reload(learning_with_variation)

        Path('llm_core/dictionary.py').touch()
        importlib.reload(dictionary)

    Path('backend/server.py').touch()
    importlib.reload(server)