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

def logits_processor(prev_tok_ids, next_tok_logits):
    return next_tok_logits

@app.route('/')
def main():
        return "test"

@app.route('/static/<path:path>')
def static_get(path):
    # Using request args for path will expose you to directory traversal attacks
    return send_from_directory('static', path)

def simulate_steam(resp):
    for item in resp.split(" "):
        time.sleep(0.5)
        token = " "+item
        yield token

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on("french")
def french(prompt):
    if "french" not in session:
        print("Starting french")
        french = L.LLM('You are a storyteller who speaks in french')
        session['french'] = french
    french = session['french']
    #Stream not yet implemented
    #resp = llm(prompt, response_format='stream', logits_processor=[logits_processor])
    print(prompt)
    resp = french(prompt, max_tokens=50, logits_processor=[logits_processor])
    print(resp)
    #Simulate generator
    emit("french", "<START>") 
    for token in simulate_steam(resp):
        emit("french", token)

@socketio.on("new-french")
def new_french():
    french = L.LLM('You are a french explorer, respond in french')
    session['french'] = french


print(socket.gethostname())

app.run(host=socket.gethostname(), port=8001)