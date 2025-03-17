from flask import Flask,render_template,request
from flask_socketio import SocketIO, emit
import subprocess
import socket
import time
import json
from flask import send_from_directory, Response
from flask import session
from stats import PieChart, StatView, LineGraph, NumericalStat
import numpy as np
import getpass

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

tts_words = {}
img_words = {}

def clean_word(s):
    return ''.join(c for c in s.lower().strip() if c.isalpha())
    
def get_app(learning_llm, L, SRS, tts, image_gen, root, port):
    app = Flask(__name__, static_folder=None)
    socketio = SocketIO(app,debug=True,cors_allowed_origins='*',async_mode='threading')
    tts_msgs = {}

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

    @app.route('/tts/<identity>/latest/<random>')
    def get_tts_msg(identity, random):
        nonlocal tts_msgs

        if identity in tts_msgs:
            return Response(tts_msgs[identity], mimetype='audio/wav')
        else:
            return 'No audio generated yet'

    @app.route('/tts/word/<word>')
    def test_img(word):
        global tts_words

        word = clean_word(word)
        if word not in tts_words:
            tts_words[word] = tts.generate_audio(word)
        
        return Response(tts_words[word], mimetype='audio/wav')

    from io import BytesIO

    @app.route('/img/word/<word>')
    def get_tts_word(word):
        global img_words

        word = clean_word(word)
        
        if word not in img_words:
            l = L.LLM('You are a picture describer who describes pictures that help language learners remember vocabulary.')
            l(f'Translate this Finnish word into English: "{word}"') # TODO: in-ctx translate (or most common meaning, or avg all meanings)
            prompt = l(f'Give me a concise description for a picture depicting the Finnish word. DO NOT include text/writing of any sort. Avoid including people if possible. The word is: "{word}"')
            print(word, '->', l.get_pretty_hist())
            img_words[word] = image_gen.generate_img(prompt)

        img = img_words[word]
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return Response(img_io, mimetype='image/png')

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')

    @socketio.on("identify")
    def identify(identity):
        session['identity'] = identity

    # http://localhost:8001/static/chat/index.html
    @socketio.on("chat-interface")
    def chat_interface(prompt):
        nonlocal tts_msgs

        if 'srs' not in session:
            session['srs'] = SRS.SRS() # TODO: in the future, load an existing user-specific SRS (or create if it doesn't exist)

        level0_mode = False

        if not level0_mode:
            if 'chat-instance' not in session:
                session['chat-inference'] = L.LLM(generate_sys_prompt(session['srs']))

            llm = session['chat-inference']
            
            s = llm(prompt, response_format='stream', max_tokens=8000, temperature=0.15)
            msg = ''
            emit("chat-interface", '<START>')
            for tok in s:
                emit("chat-interface", tok)
                msg += tok
            emit("chat-interface", '<END>')
            tts_msgs[session['identity']] = tts.generate_audio(msg) # TODO try catch for invalid msg
            emit("chat-interface", '<TTS>')
        else:
            # The process:
            # TODO: intro prompt
            # User chooses a subject
            # LLM makes a simple sentence in target language
            # LLM asks a question in native language
            # User responds in native language
            # LLM gives reasoning on response in native language
            # LLM makes another simple sentence
            # LLM asks a question
            # ...

            # The code:
            # check if question already asked (sentence and question variables exist)
            # if so, provide reasoning
            # make new sentence (and store variable)
            # ask new question  (and store variable)
            # ...
            
            if 'learning' not in session:
                session['learning-llm'] = learning_llm.learning_llm(learning_llm.get_vocab())
                
            learn = session['learning-llm']

            if 's' not in session:
                session['s'] = ''
                session['q'] = ''
                session['a'] = ''
            else:
                # evaluate
                s_string = session['s']
                q_string = session['q']
                a = session['a']
                e = learn.evaluate(s_string, q_string, a, prompt)
                emit("chat-interface", '<START>')
                for tok in e:
                    emit("chat-interface", tok)
                emit("chat-interface", '<END>')
                print("Answer correct:", learn.grade()['correct'])

            # target word selection 
            target_word = 'koira'
            # reset strings
            s_string = ''
            q_string = ''
            # sentence
            s, sentence = learn.get_sentence(target_word)
            emit("chat-interface", '<START>')
            for tok in sentence:
                emit("chat-interface", tok)
                s_string += tok
            emit("chat-interface", "\n\n")
            print('s_string:', s_string)
            # question
            q = learn.get_question(target_word, s, s_string)
            for tok in q:
                emit("chat-interface", tok)
                q_string += tok
            emit("chat-interface", '<END>')
            print('q_string:', q_string)
            a = learn.get_answer(target_word)['Answer']
            print('answer:', a)
            # save session variables
            session['s'] = s_string
            session['q'] = q_string
            session['a'] = a

    def app_fn():
        nonlocal app, port
        print(f"Run this on your local machine in WSL or Git Bash:")
        print(f"ssh -L {port}:{socket.gethostname()}:{port} {getpass.getuser()}@dh-mgmt2.hpc.msoe.edu")
        app.run(host=socket.gethostname(), port=port, debug=False)

    return app_fn