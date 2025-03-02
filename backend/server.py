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
from user import User

def generate_sys_prompt(srs):
    TEACHER_NAME = 'Rose' # localized to target language (regular 'e' for Finnish)
    LEARNER_NAME = 'Lucas' # obtained from user profile

    # TODO: eventually get this from srs
    allowed_vocab = [
        # greetings
        'terve', 'hei',

        # nouns
        'talo',     # house
        'vesi',     # water
        'ystävä',   # friend
        'huomenta', # morning
        'velho',    # wizard
        'suomi',    # Finland
        'koira',    # dog
        'nimi',     # name

        # singular possessive nouns for 'nimi'
        'nimeni',   # first person "my name"
        'nimesi',   # second person "your name"
        'nimensä',  # third person "his name"

        # singular posessive nous for 'ystävä'
        'ystäväni',  # first person
        'ystäväsi',  # second person
        'ystävänsä', # third person

        # adjectives
        'vanha',       # old
        'hyvää',       # good
        'suomalainen', # Finnish
        'mukava',      # nice

        # pronouns, posesives, "to be" verbs
        'minä', 'minun', 'olen', 'olenko', # first person
        'sinä', 'sinun', 'olet', 'oletko', # second person
        'hän', 'hänen', 'on', 'onko',      # third person

        # names
        'matti', 'aleksi', 'sami', TEACHER_NAME.lower(), LEARNER_NAME.lower(),

        # useful words
        'kyllä', # yes
        'ei', # no
        'mitä', # "what/how" as in "what did you say?" or "how are you" -- about more abstract things
        'mikä', # "what" as in "what is this?" or "what is your name?" -- about specific things
    ]

    for v in allowed_vocab:
        srs.add_card(v)

    # NOTE: maybe review should err if the card doesn't exist?
    # srs.review_card("some card that doesn't exist", "good") # => KeyError

    sys_prompt = (
        'You are a Finnish teaching assistant named Rose. I am a Finnish learner named Lucas.' +
        '\nRespond to future messages with SINGLE, SHORT sentences and nothing else. ' +
        'Use a lot of emojis. Use newlines to end messages.' +
        '\n\nThis is the set of allowed vocab you can draw from for responses:\n{' + ', '.join(allowed_vocab) + '}' +
        '\n\nIMPORTANT: All word usage must be grammatically correct Finnish -- if the available words cannot express something, then DON\'T try expressing it.'
    )

    return sys_prompt

def get_app(L, SRS, root, port):
    app = Flask(__name__, static_folder=None)
    socketio = SocketIO(app,debug=True,cors_allowed_origins='*',async_mode='threading')
    
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

    @app.route('/static/<path:subpath>')
    def static_get(subpath):
        # Using request args for path will expose you to directory traversal attacks
        print(f'{root}/static', subpath)
        return send_from_directory(f'{root}/static', subpath)

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')

    @socketio.on("identify")
    def identify(identity):
        session['identity'] = identity
        user = User.load(identity)
        session['user'] = user
    @socketio.on("chat-interface")
    def chat_interface(prompt):
        """
        if 'srs' not in session:
            session['srs'] = SRS.SRS() # TODO: in the future, load an existing user-specific SRS (or create if it doesn't exist)
        """
        if 'chat-instance' not in session:
            session['chat-inference'] = L.LLM(generate_sys_prompt(session['user'].get_SRS()))

        llm = session['chat-inference']

        s = llm(prompt, response_format='stream', max_tokens=8000, temperature=0.15)
        res = ""
        emit("chat-interface", '<START>')
        for tok in s:
            emit("chat-interface", tok)
            res += tok
        emit("chat-interface", '<END>')
        session['user'].update_daily_known_word_count(len(res.split(" ")))
        session['user'].update_messages(prompt, res)
        session['user'].save()

    # @socketio.on("french")
    # def french(prompt):
    #     if 'french' not in session:
    #         session['french'] = L.LLM('You are a storyteller who speaks in french')

    #     french = session['french']
        
    #     print(f"{session['identity']} sent : {prompt}")
    #     resp = french(prompt, response_format='stream', max_tokens=200, logits_processor=[logits_processor])
    #     emit("french", "<START>") 
    #     for token in resp:
    #         emit("french", token)
    #     emit("french", "<END>") 


    # @socketio.on("new-french")
    # def new_french():
    #     french = L.LLM('You are a storyteller who speaks in french')
    #     session['french'] = french

    def app_fn():
        nonlocal app, port
        print(f"Run this on your local machine in WSL or Git Bash:")
        print(f"ssh -L {port}:{socket.gethostname()}:{port} {getpass.getuser()}@dh-mgmt2.hpc.msoe.edu")
        app.run(host=socket.gethostname(), port=port, debug=False)

    return app_fn