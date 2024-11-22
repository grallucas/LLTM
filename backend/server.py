from flask import Flask,render_template,request
from flask_socketio import SocketIO, emit
import subprocess
from flask_sock import Sock 
import llm as L
#    print(f"ssh -L 8001:{host}:8001 {getpass.getuser()}@dh-mgmt2.hpc.msoe.edu")

app = Flask(__name__)
socketio = SocketIO(app,debug=True,cors_allowed_origins='*',async_mode='eventlet')
sock = Sock(app)


def logits_processor(prev_tok_ids, next_tok_logits):
    return next_tok_logits

@app.route('/')
def main():
        return "test"

@sock.route('/chat/ws')
def echo(ws):
    llm = L.LLM('You are a British butler. Start every answer with "you"')
    while True:
        data = ws.receive()
        resp = llm(data, max_tokens=20, logits_processor=[logits_processor])
        ws.send(resp)

app.run(port=8081)