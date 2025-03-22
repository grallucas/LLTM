import sys
import socket
import getpass
from pathlib import Path
from flask import Flask, render_template, request, send_from_directory, Response, session
from flask_socketio import SocketIO, emit

import llm as L
from models import generate_img, generate_tts
import lexicon
import translate
import feedback
import chat

sys.path.append("./llm_core")
import learning_with_variation

app = Flask(__name__, static_folder=None)
socketio = SocketIO(app, debug=True, cors_allowed_origins='*', async_mode='threading')

ROOT = Path.cwd().as_posix()
TTS_URL, IMG_GEN_URL = sys.argv[-1].split(',')
PORT = sys.argv[-2]
L.TOKEN_COUNT_PATH = '/data/ai_club/team_3_2024-25/tokcounts2/'

# TODO: cache on disk
tts_words = {}
img_words = {}
lexicon_words = {}

# cached in memory
tts_msgs = {}
ctx_msgs = {}
feedback_msgs = {}

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

@app.route('/lexicon/<word>')
def get_word_info(word):
    word = clean_word(word)
    if word not in lexicon_words:
        lexicon_words[word] = lexicon.lookup_word(word, 'Finnish')

    return lexicon_words[word]

@app.route('/ctxtranslate/<identity>/<word>')
def translate_word(identity, word):
    if identity not in ctx_msgs:
        return 'No context yet'

    word = clean_word(word)

    if word not in lexicon_words:
        lexicon_words[word] = lexicon.lookup_word(word, 'Finnish')

    translated_word, explanation, breakdown = translate.translate_in_ctx(ctx_msgs[identity], word, lexicon_words[word])

    return {
        'translated': translated_word,
        'explanation': explanation,
        'breakdown': breakdown
    }

@app.route('/img/word/<word>')
def get_img_word(word):
    word = clean_word(word)
    if word not in img_words:
        print('generating img for', word)
        l = L.LLM('You are a picture describer who describes pictures that help language learners remember vocabulary.')
        l(f'Concisely Translate this Finnish word into English: "{word}"') # TODO: in-ctx translate (or most common meaning, or avg all meanings)
        l('What might be a good simple picture to help me remember this word?')
        prompt = l(f'That sounds good to me. Give me a concise description for that picture depicting the word to help me remember it. Absolutely DO NOT include text/writing/symbols of any sort. Avoid including people if possible.')
        print(l._hist)
        img_words[word] = generate_img(prompt, IMG_GEN_URL)

    img = img_words[word]
    return Response(img, mimetype='image/png')

@app.route('/feedback/<identity>/generate', methods=['POST'])
def gen_feedback(identity):
    prompt = request.get_data().decode()

    if identity not in feedback_msgs:
        feedback_msgs[identity] = []

    feedback_msgs_idx = feedback_msgs[identity].__len__()

    words, incorrect, state = feedback.grade_per_word(prompt)
    per_word = {}
    for i in incorrect:
        per_word[i] = (state, words) # save data to stream explanations later

    feedback_msgs[identity].append(per_word)

    return {
        'words': words,
        'word_feedbacks': incorrect,
        'feedback_id': feedback_msgs_idx
    }

@app.route('/feedback/<identity>/get/<idx>')
def get_feedback(identity, idx):
    feedback_msgs_idx, idx = [int(x) for x in idx.split(',')]

    # print('-------------------------------------------')

    if type(feedback_msgs[identity][feedback_msgs_idx][idx]) is tuple:
        state, words = feedback_msgs[identity][feedback_msgs_idx][idx]
        
        # TODO: stream this data to the client in the future?
        exp = feedback.get_word_feedback(idx, words, state)
        exp_str = ''
        for t in exp: exp_str += t
        feedback_msgs[identity][feedback_msgs_idx][idx] = exp_str

    # print(feedback_msgs[identity][feedback_msgs_idx][idx])
    # print('-------------------------------------------')

    return {
        'feedback': feedback_msgs[identity][feedback_msgs_idx][idx]
    }

@socketio.on("identify")
def identify(identity):
    session['identity'] = identity

@socketio.on("chat-interface")
def chat_interface(prompt):
    if 'level' not in session:
        session['level'] = 0 #TODO change session level in UI
    if session['level'] == 0:
        level0(prompt)
    if session['level'] == 1:
        level1(prompt)

def level1(prompt):
    if 'chat' not in session:
        session['chat'] = chat.make_chat_llm(chat.allowed_vocab)
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

    ctx_msgs[session['identity']] = f'A:\n{prompt}\n\nB:{msg}'

def level0(prompt):
    if 'learning' not in session:
        session['learning-llm'] = learning_with_variation.learning_llm(learning_with_variation.get_vocab())
            
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
            print("Answer correct:", learn.grade())

        # target word selection 
        target_word = 'koira' # TODO: Get target word from SRS
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
        a = learn.get_answer(target_word)
        print('answer:', a)
        # save session variables
        session['s'] = s_string
        session['q'] = q_string
        session['a'] = a

print(f"Run this on your local machine in WSL or Git Bash:")
print(f"ssh -L {PORT}:{socket.gethostname()}:{PORT} {getpass.getuser()}@{socket.gethostname()}.hpc.msoe.edu")
app.run(host=socket.gethostname(), port=PORT, debug=False)
