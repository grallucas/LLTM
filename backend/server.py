from flask import Flask,render_template,request
from flask_socketio import SocketIO, emit
import subprocess
import socket
import time
import json
from flask import send_from_directory
from flask import session
from stats import PieChart, StatView, LineGraph, NumericalStat
import numpy as np
import getpass

import llm as L

app = Flask(__name__)
socketio = SocketIO(app,debug=True,cors_allowed_origins='*',async_mode='threading')
L.LLM("")

def logits_processor(prev_tok_ids, next_tok_logits):
    return next_tok_logits

@app.route('/')
def main():
        return "test"

@app.route('/api/stats/<language>')
def stats_api(language):
    if language == 'FRENCH':
        pie = PieChart("Test")
        pie.add_slice("test1", 0.7)
        pie.add_slice('test2',0.3)
        sv = StatView()
        sv.add_graph(pie.construct())
        
        line = LineGraph("test2")
        line2 = LineGraph("test3")

        num1 = NumericalStat("Test4", 12)
        num2 = NumericalStat("Test5", 123123)
        num3 = NumericalStat("Test6", 0)
        sv.add_number(num1.construct())
        sv.add_number(num2.construct())
        sv.add_number(num3.construct())

        X = np.arange(-5,6,1)
        Y = X**2
        Y2 = np.absolute(X)

        for x, y in zip(X,Y):
            line.add_point(str(x), int(y))
        for x, y in zip(X,Y2):
            line2.add_point(str(x), int(y))
        sv.add_graph(line.construct())
        sv.add_graph(line2.construct())

        print(Y)
        return sv.json()

# @app.route('/stats/<path:path>')
# def static_stats(path):
#     return send_from_directory('stats', path)


# @app.route('/webui/<path:path>')
# def static_webui(path):
#     return send_from_directory('webUI', path)

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

@socketio.on("french")
def french(prompt):
    if 'french' not in session:
        session['french'] = L.LLM('You are a storyteller who speaks in french')

    french = session['french']
    
    print(f"{session['identity']} sent : {prompt}")
    resp = french(prompt, response_format='stream', max_tokens=200, logits_processor=[logits_processor])
    emit("french", "<START>") 
    for token in resp:
        emit("french", token)
    emit("french", "<END>") 


@socketio.on("new-french")
def new_french():
    french = L.LLM('You are a storyteller who speaks in french')
    session['french'] = french

print(f"Run this on your local machine in WSL or Git Bash:")
print(f"ssh -L 8001:{socket.gethostname()}:8001 {getpass.getuser()}@dh-mgmt2.hpc.msoe.edu")

app.run(host=socket.gethostname(), port=8001)