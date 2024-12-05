from flask import Flask,render_template,request
from flask_socketio import SocketIO, emit
import subprocess
import llm as L
import socket
import time
import json

app = Flask(__name__)
socketio = SocketIO(app,debug=True,cors_allowed_origins='*',async_mode='threading')

french = L.LLM('You are a french explorer, respond in french')

def logits_processor(prev_tok_ids, next_tok_logits):
    return next_tok_logits

@app.route('/')
def main():
        return "test"

def simulate_steam(resp):
    for item in resp.split(" "):
        time.sleep(0.5)
        yield item

@socketio.on("french")
def echo(prompt, conversation_id):
    #Stream not yet implemented
    #resp = llm(prompt, response_format='stream', logits_processor=[logits_processor])
    resp = french(prompt,  logits_processor=[logits_processor])
    print(resp)
    #Simulate generator
    for token in simulate_steam(resp):
        emit(conversation_id, token)
    

print(socket.gethostname())

app.run(host=socket.gethostname(), port=8001)