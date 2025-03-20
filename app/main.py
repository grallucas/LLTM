import sys
import socket
import getpass
from pathlib import Path
from flask import Flask, render_template, request, send_from_directory, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder=None)
socketio = SocketIO(app, debug=True, cors_allowed_origins='*', async_mode='threading')

ROOT = Path.cwd().as_posix()
IMG_GEN_URL, TTS_URL = sys.argv[-1].split(',')
PORT = sys.argv[-2]

@app.route('/')
def main():
    return "http://localhost:8001/static/chat/index.html"

@app.route('/api/stats/<language>')
def stats_api(language):
    return 'temp'

@app.route('/static/<path:subpath>')
def static_get(subpath):
    return send_from_directory(f'{ROOT}/static', subpath)

@app.route('/tts/<identity>/latest/<idx>')
def get_tts_msg(identity, idx):
    return 'temp'

@app.route('/tts/word/<word>')
def get_tts_word(word):
    return 'temp'

@app.route('/dictionary/<word>')
def get_word_info(word):
    return 'temp'

@app.route('/img/word/<word>')
def get_img_word(word):
    return 'temp'

@socketio.on('connect')
def handle_connect():
    pass

@socketio.on("identify")
def identify(identity):
    pass

@socketio.on("chat-interface")
def chat_interface(prompt):
    emit("chat-interface", '<START>')
    emit("chat-interface", '<END>')
    emit("chat-interface", '<TTS>')

print(f"Run this on your local machine in WSL or Git Bash:")
# print(f"ssh -L {PORT}:{socket.gethostname()}:{PORT} {getpass.getuser()}@dh-mgmt2.hpc.msoe.edu")
print(f"ssh -L {PORT}:{socket.gethostname()}:{PORT} {getpass.getuser()}@{socket.gethostname()}.hpc.msoe.edu")
app.run(host=socket.gethostname(), port=PORT, debug=False)
