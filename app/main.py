import sys
import socket
import getpass
from pathlib import Path
from flask import Flask, render_template, request, send_from_directory, Response, session
from flask_socketio import SocketIO, emit
import time
import os
import json
import string

import llm as L
from models import generate_img, generate_tts
import lexicon
import translate
import feedback
import chat
import leveled_learning
import conversation_learning
import language_progress

import SRS
import datetime

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

# Global Variables (cached in memory)
tts_msgs = {}
ctx_msgs = {}
feedback_msgs = {}
global_srs = {} #{identity : srs}
global_language_progress = {} #{identity : language_progress}
global_mode = {} #{identity : mode} (modes are strings, 'conversation' or 'review' or 'learn')
session_language = 'Finnish'

# Path settings
USER = getpass.getuser()
save_path = './ColloquyLanguageLearning/saves'
home_path = '/home'
save_path = os.path.join(home_path, USER, save_path)

#TODO:
    #check srs updates
        #spam same word -> other words don't get removed
        #words should be removed after correct enough
        #try marking all as incorrect and make sure they DONT go away

#TODO catch the response format fail 

#TODO learning mode = review + learn mode, add new card button

#TODO conversation mode with NO SRS for NOW

#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*

#TODO counter for incorrect words before reviewing as incorrect
#TODO conversation mode WITHOUT review panel and .10x srs weight
#       Note: fsrs does NOT have a way to add weight to updates. Workaround needed or drop

tomorrow = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1) #datetime.now is not timezone aware

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
        lexicon_words[word] = lexicon.lookup_word(word, session_language)

    return lexicon_words[word]

@app.route('/ctxtranslate/<identity>/<word>')
def translate_word(identity, word):
    if identity not in ctx_msgs:
        return {
            'translated': None,
            'explanation': 'No context yet',
            'breakdown': None
        }

    word = clean_word(word)

    if word not in lexicon_words:
        lexicon_words[word] = lexicon.lookup_word(word, session_language)

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
        l(f'Concisely Translate this {session_language} word into English: "{word}"') # TODO: in-ctx translate (or most common meaning, or avg all meanings)
        l(
            'What might be a good simple picture to help me remember this word? '
            'Absolutely DO NOT include text/writing/symbols of any sort. Do not include hands. '
            'Avoid including people if possible. '
            # 'If there is no obvious description for a picture, then connect the Finnish word to a common, similar-sounding English one (e.g., "joka" -> "a joker pointing to *that* card"). '
            'Finally, keep the image as simple as possible.'
        )
        prompt = l(f'That sounds good to me. Give me a concise description for that picture depicting the word to help me remember it.')
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

    #update srs based on feedback
    clean_words = [clean_word(word) for word in words]
    srs_correct, srs_incorrect = get_correct_incorrect(clean_words, incorrect)
    if global_mode[identity] == 'review' or global_mode[identity] == 'learn':
        srs_update(srs_correct, srs_incorrect, global_srs[identity])

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

@app.route('/srs/review/<identity>/<word>')
def srs_review_route_again(identity, word):
    srs = global_srs[identity]
    print('reviewing in srs route. Word, "again":', word, )
    srs.review_card(word, 'again') 
    return ''

@socketio.on("identify")
def identify(identity):
    session['identity'] = identity

@socketio.on("chat-interface")
def chat_interface(prompt):
    if global_mode[session['identity']] == 'conversation':
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
    if global_mode[session['identity']] == 'review':
        learning_convo(prompt, session['identity'], session['learning-llm'])
    if global_mode[session['identity']] == 'learn':
        learning_convo(prompt, session['identity'], session['learning-llm'])
    

def initialize(identity):
    PATH = save_path
    if os.path.exists(PATH):
        # reload saved srs and language progress
        srs_path = os.path.join(PATH, 'srs.json')
        with open(srs_path, 'r') as file:
            srs_json_string = json.load(file)
            srs = SRS.SRS()
            srs.deserialize(srs_json_string)
            global_srs[identity] = srs
        language_progress_path = os.path.join(PATH, 'language_progress.json')
        with open(language_progress_path, 'r') as file:
            language_progress_json_string = json.load(file)
            lp = language_progress.language_progress([], session_language)
            global_language_progress[identity] = lp
    else:
        lp = language_progress.language_progress(language_progress.intro_words, session_language)
        global_language_progress[identity] = lp
        srs = SRS.SRS()
        global_srs[identity] = srs
        
def add_words(num_words : int, srs : SRS.SRS, lp : language_progress.language_progress) -> None:
    for i in range(num_words):
        word = lp.get_new_word()
        word = clean_word(word)
        print('adding word:', word)
        srs.add_card(word)

@socketio.on('conversation-mode')
def conversation_mode():
    global_mode[session['identity']] = 'conversation' 
    initialize(session['identity'])
    chat_interface('You start. Keep this interactive by asking ME questions.')

@socketio.on('review-mode')
def review_mode():
    global_mode[session['identity']] = 'review' 
    initialize(session['identity'])
    if 'learning-llm' not in session:
        session['learning-llm'] = conversation_learning.learning_llm()
    # update review screen with new due words
    update_review_panel(global_srs[session['identity']])
    learning_convo('', session['identity'], session['learning-llm']) 

@socketio.on('learn-mode')
def learn_mode():
    global_mode[session['identity']] = 'learn'
    initialize(session['identity'])
    if 'learning-llm' not in session:
        session['learning-llm'] = conversation_learning.learning_llm()
    add_words(5, global_srs[session['identity']], global_language_progress[session['identity']])
    update_review_panel(global_srs[session['identity']])
    learning_convo('', session['identity'], session['learning-llm'])


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

def learning_convo(prompt, identity, learning_llm):
    if prompt == '':
        # convo_introduction() TODO let's do something better than a big text wall
        # llm starts with question
        target_word = get_target_word(global_srs[identity])
        q_string = learning_convo_question(target_word, learning_llm)
        ctx_msgs[identity] = f'A:\n{prompt}\n\nB:{q_string}'
        tts_msgs[identity] = generate_tts(q_string, TTS_URL)
        emit("chat-interface", '<TTS>')
    else:
        # respond to question
        s_string = learning_convo_sentence(prompt, learning_llm)
        ctx_msgs[identity] = f'A:\n{prompt}\n\nB:{s_string}'
        # send question
        target_word = get_target_word(global_srs[identity])
        q_string = learning_convo_question(target_word, learning_llm)
        ctx_msgs[identity] = f'A:\n{prompt}\n\nB:{s_string}'
        tts_msgs[identity] = generate_tts(s_string + '\n \n \n' + q_string, TTS_URL)
        emit("chat-interface", '<TTS>')
        print('CTX HISTORY:', ctx_msgs)

def get_target_word(srs):
    target_word = ''
    if len(srs.get_due_before_date(tomorrow)) != 0:
        target_word = srs.get_due_before_date(tomorrow)[0] 
    elif srs.num_words() != 0:
        list(srs.get_words())[0]
    else:
        return '' #TODO take lp and generate a new word
    print('target word =', target_word) #TODO clean up
    return target_word

def learning_convo_sentence(prompt, learning_llm):
    s = learning_llm.get_sentence(prompt)
    s_string = ''
    emit("chat-interface", '<START>')
    for tok in s:
        emit("chat-interface", tok)
        s_string += tok
    emit("chat-interface", '<END>')
    emit("chat-interface", "<NO-TTS>")
    print('s_string:', s_string)
    return s_string

def learning_convo_question(target_word, learning_llm):
    q = learning_llm.get_question(target_word)
    q_string = ''
    emit("chat-interface", '<START>')
    for tok in q:
        emit("chat-interface", tok)
        q_string += tok
    emit("chat-interface", '<END>')
    print('q_string:', q_string)
    return q_string

def convo_introduction():
    intro = ("Welcome to the review mode! Here you will respond to questions and write your own "
            "just like in a conversation. Your list of words to review is shown at the top. "
            "Use words correctly to get them removed from your to-do list, while incorrect "
            "words will be added to it. Don't worry though, making mistakes is part of the "
            "process! Just try to get through the whole list at your own pace and the "
            "learning will happen naturally.")

    emit("chat-interface", '<START>')
    emit("chat-interface", intro)
    emit("chat-interface", '<END>')
    emit("chat-interface", '<NO-TTS>')


'''
This method updates the session's SRS object based on 
two lists: [correct] and [incorrect]'''
def srs_update(correct : list, incorrect : list, srs) -> None:
    print('srs currently due words:', srs.get_due_before_date(tomorrow)) #TODO clean up
    print('srs_update correct:', correct)
    print('srs_update incorrect:', incorrect)
    for word in incorrect:
        srs.review_card(word, 'again')
    for word in correct:
        srs.review_card(word, 'good')
    print('srs due words after srs_update:', srs.get_due_before_date(tomorrow)) #TODO clean up

'''
This method is a helper for extracting the correct and incorrect words from the grade_per_word method.
It should only be used in the gen_feedback method before the srs_update call.
Functionality:
grade_per_word returns a tuple of (words, incorrect, state) for a given sentence. 
  words is a list of the words in the sentence
  incorrect is a list of indices in words where the word is incorrect
  state is the LLM state at the grading, which isn't needed for this function
This helper method creates two new lists from words and incorrect, with one containing the correct
words and the other containing the incorrect words'''
def get_correct_incorrect(words, incorrect_indices):
    incorrect = [words[i] for i in incorrect_indices]
    correct = [word for word in words if word not in incorrect]
    print('correct:', correct)
    print('incorrect:', incorrect)
    return (correct, incorrect)

'''
This method prepares the srs due words in a string format to be split on the
javascript end (main.js)'''
@app.route('/srs-due-before-tomorrow/<identity>')
def update_review_panel(identity):
    string_words_due = ''
    if global_mode[identity] != 'conversation':
        time.sleep(5)
        srs = global_srs[identity]
        words_due = srs.get_due_before_date(tomorrow)
        for word in words_due:
            string_words_due = string_words_due + word + ' '
        print('returning srs due words string:', string_words_due)
    return string_words_due

#TODO make this a call to the js side to the route above ^^^^^
def update_review_panel(srs):
    words_due = srs.get_due_before_date(tomorrow)
    string_words_due = ''
    for word in words_due:
        string_words_due = string_words_due + word + ' '
    emit('srs-update', string_words_due)

# @app.route('/save-on-disconnect/<identity>')
@socketio.on('disconnect')
def save_on_disconnect():
    identity = session['identity']
    srs_serialized = global_srs[identity].serialize()
    print(srs_serialized)
    language_progress_serialized = global_language_progress[identity].serialize()
    print(language_progress_serialized)
    PATH = save_path
    if not os.path.exists(PATH):
        os.makedirs(PATH)
    srs_file_path = os.path.join(PATH, 'srs.json')
    with open(srs_file_path, "w") as file:
        json.dump(srs_serialized, file, indent=4)
    language_progress_path = os.path.join(PATH, 'language_progress.json')
    with open(language_progress_path, "w") as file:
        json.dump(language_progress_serialized, file, indent=4)
    print('save complete')
    return ''


print(f"Run this on your local machine in WSL or Git Bash:")
print(f"ssh -L {PORT}:{socket.gethostname()}:{PORT} {getpass.getuser()}@{socket.gethostname()}.hpc.msoe.edu")
app.run(host=socket.gethostname(), port=PORT, debug=False)
