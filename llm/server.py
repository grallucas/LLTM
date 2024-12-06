from flask import Flask,render_template,request
from flask_socketio import SocketIO, emit
import subprocess
import llm as L
import socket
import time
import json
from flask import send_from_directory
from flask import session

app = Flask(__name__)
socketio = SocketIO(app,debug=True,cors_allowed_origins='*',async_mode='threading')
L.LLM("")

def logits_processor(prev_tok_ids, next_tok_logits):
    return next_tok_logits

@app.route('/')
def main():
        return "test"

@app.route('/static/<path:path>')
def static_get(path):
    # Using request args for path will expose you to directory traversal attacks
    return send_from_directory('static', path)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on("identify")
def identify(identity):
    session['identity'] = identity
    french = L.LLM('You are a storyteller who speaks in french')
    session['french'] = french

@socketio.on("french")
def french(prompt):
    french = session['french']
    
    print(f"{session['identity']} sent : {prompt}")
    resp = french(prompt, response_format='stream', max_tokens=50, logits_processor=[logits_processor])
    emit("french", "<START>") 
    for token in resp:
        emit("french", token)
    emit("french", "<END>") 


@socketio.on("new-french")
def new_french():
    french = L.LLM('You are a storyteller who speaks in french')
    session['french'] = french



print(socket.gethostname())

app.run(host=socket.gethostname(), port=8001)