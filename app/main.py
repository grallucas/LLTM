import sys
import socket
import getpass
from pathlib import Path
from flask import Flask, render_template, request, send_from_directory, Response
from flask_socketio import SocketIO, emit
from flask import session

import llm as L
from models import generate_img, generate_tts

app = Flask(__name__, static_folder=None)
socketio = SocketIO(app, debug=True, cors_allowed_origins='*', async_mode='threading')

ROOT = Path.cwd().as_posix()
TTS_URL, IMG_GEN_URL = sys.argv[-1].split(',')
PORT = sys.argv[-2]
L.TOKEN_COUNT_PATH = '/data/ai_club/team_3_2024-25/tokcounts2/'

# TODO: cache on disk
tts_words = {}
img_words = {}
# TODO: cache in memory
tts_msgs = {}

def clean_word(s):
    return ''.join(c for c in s.lower().strip() if c.isalpha())

@app.route('/')
def main():
    print(session)
    return "http://localhost:8001/static/chat/index.html"

@app.route('/api/stats/<language>')
def stats_api(language):
    return 'temp'

@app.route('/static/<path:subpath>')
def static_get(subpath):
    return send_from_directory(f'{ROOT}/static', subpath)

@app.route('/tts/<identity>/latest/<idx>')
def get_tts_msg(identity, idx):
    # For now idx is just a random number so the browser doesn't cache old tts audio.
    if identity in tts_msgs:
        return Response(tts_msgs[identity], mimetype='audio/wav')
    else:
        return 'No audio generated yet'

@app.route('/tts/word/<word>')
def get_tts_word(word):
    word = clean_word(word)

    if word not in tts_words:
        tts_words[word] = generate_tts(word, TTS_URL)
    
    return Response(tts_words[word], mimetype='audio/wav')

@app.route('/dictionary/<word>')
def get_word_info(word):
    return 'temp'

@app.route('/img/word/<word>')
def get_img_word(word):
    if word not in img_words:
        l = L.LLM('You are a picture describer who describes pictures that help language learners remember vocabulary.')
        l(f'Concisely Translate this Finnish word into English: "{word}"') # TODO: in-ctx translate (or most common meaning, or avg all meanings)
        l('What might be a good simple picture to help me remember this word?')
        prompt = l(f'That sounds good to me. Give me a concise description for that picture depicting the word to help me remember it. Absolutely DO NOT include text/writing/symbols of any sort. Avoid including people if possible.')
        print(word, '->', l._hist)
        img_words[word] = generate_img(prompt, IMG_GEN_URL)

    img = img_words[word]
    return Response(img, mimetype='image/png')

@socketio.on("identify")
def identify(identity):
    session['identity'] = identity

@socketio.on("chat-interface")
def chat_interface(prompt):
    if 'chat' not in session:
        session['chat'] = L.LLM('You are a Finnish language teacher.')
    llm = session['chat']

    s = llm(prompt, response_format='stream', max_tokens=8000, temperature=0.15)
    msg = ''
    emit("chat-interface", '<START>')
    for tok in s:
        emit("chat-interface", tok)
        msg += tok
    emit("chat-interface", '<END>')
    tts_msgs[session['identity']] = generate_tts(msg, TTS_URL)
    emit("chat-interface", '<TTS>')

print(f"Run this on your local machine in WSL or Git Bash:")
print(f"ssh -L {PORT}:{socket.gethostname()}:{PORT} {getpass.getuser()}@{socket.gethostname()}.hpc.msoe.edu")
app.run(host=socket.gethostname(), port=PORT, debug=False)
