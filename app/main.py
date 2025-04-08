import sys
import socket
import getpass
from pathlib import Path
from flask import Flask, render_template, request, send_from_directory, Response, session
from flask_socketio import SocketIO, emit
import time

import llm as L
from models import generate_img, generate_tts
import lexicon
import translate
import feedback
import chat
import leveled_learning
import conversation_learning

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

# cached in memory
tts_msgs = {}
ctx_msgs = {}
feedback_msgs = {}
global_srs = {} #{identity : srs}

#TODO learn mode with new words on initialization 
#TODO Duolingo beginner words

#TODO conversation mode WITHOUT review panel and .10x srs weight
#       Note: fsrs does NOT have a way to add weight to updates. Workaround needed

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
        lexicon_words[word] = lexicon.lookup_word(word, 'Finnish')

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
    correct, incorrect = get_correct_incorrect(words, incorrect)
    srs_update(correct, incorrect, global_srs[identity])

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
    print('reviewing in srs route. Word, "again":', word, ) #TODO clean up
    srs.review(word, 'again')

@socketio.on("identify")
def identify(identity):
    session['identity'] = identity

@socketio.on("chat-interface")
def chat_interface(prompt):
    if session['level'] == 'conversation':
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
        # srs_update(srs_correct_incorrect['correct'], srs_correct_incorrect['incorrect']) #TODO clean up
    if session['level'] == 'review':
        print('before prompt')
        learning_convo(prompt)
        print('after prompt')
        # srs_update(srs_correct_incorrect['correct'], srs_correct_incorrect['incorrect']) #TODO clean up
        # update review screen with new due words
        update_review_panel(global_srs[session['identity']])
    if session['level'] == 'learn':
        learning_convo(prompt)
        update_review_panel(global_srs[session['identity']])
        # srs_update(srs_correct_incorrect['correct'], srs_correct_incorrect['incorrect']) #TODO clean up
    

def initialize(identity, level='conversation'):
    if 'level' not in session:
        session['level'] = level #TODO global level of identidies
    if identify not in global_srs:
        srs = SRS.SRS()
        srs.add_card('koira')
        srs.add_card('velho')
        srs.add_card('uusi')
        srs.add_card('vanha')
        srs.add_card('sinulla')
        global_srs[identity] = srs #TODO updated correctly?


@socketio.on('conversation-mode')
def conversation_mode():
    initialize('conversation', session['identity'])
    chat_interface('You start. Keep this interactive by asking ME questions.')

@socketio.on('review-mode')
def review_mode():
    initialize('review', session['identity'])
    # update review screen with new due words
    update_review_panel(session['srs'])
    learning_convo('You start. Keep this interactive by asking ME questions.')

@socketio.on('learn-mode')
def learn_mode():
    initialize('learn', session['identity'])
    learning_convo('You start. Keep this interactive by asking ME questions.')


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

def jeopardy(prompt):
    if 'learning-llm' not in session:
        session['learning-llm'] = leveled_learning.learning_llm(leveled_learning.get_vocab_qs())
            
    learn = session['learning-llm']

    if 's' not in session:
        session['s'] = ''
        session['q'] = ''
        session['a'] = ''
    else:
        # evaluate PRIOR answer if it exists
        s_string = session['s']
        q_string = session['q']
        a = session['a']
        e = learn.evaluate(s_string, q_string, a, prompt)
        emit("chat-interface", '<START>')
        for tok in e:
            emit("chat-interface", tok)
        emit("chat-interface", '<END>')
        emit("chat-interface", '<NO-TTS>')
        print("Answer correct:", learn.grade())

    # reset strings
    s_string = ''
    q_string = ''
    # target word selection 
    # target_word = getTargetWord(session['']) TODO: get from SRS
    target_word = 'koira'
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

    tts_msgs[session['identity']] = generate_tts(s_string, TTS_URL)
    emit("chat-interface", '<TTS>')

    ctx_msgs[session['identity']] = f'A:\n{prompt}\n\nB:{s_string}'

    print('q_string:', q_string)
    a = learn.get_answer(target_word)
    print('answer:', a)
    # save session variables
    session['s'] = s_string
    session['q'] = q_string
    session['a'] = a

def learning_convo(prompt):
    #initialize
    if 'learning-llm' not in session:
        session['learning-llm'] = conversation_learning.learning_llm()
        convo_introduction()
    if 'wait' not in session:
        session['wait'] = 2
        # llm starts with question
        target_word = get_target_word(session['srs'])
        q_string = learning_convo_question(target_word)
        tts_msgs[session['identity']] = generate_tts(q_string, TTS_URL)
        emit("chat-interface", '<TTS>')

    # Converse on turn (wait for 2 messages before sending)
    if session['wait'] > 1:
        session['wait'] = session['wait'] - 1
    else:
        # respond to question
        s_string = learning_convo_sentence(prompt)
        ctx_msgs[session['identity']] = f'A:\n{prompt}\n\nB:{s_string}'
        # send question
        target_word = get_target_word(session['srs'])
        q_string = learning_convo_question(target_word)
        ctx_msgs[session['identity']] = f'A:\n{prompt}\n\nB:{s_string}'
        tts_msgs[session['identity']] = generate_tts(s_string + '\n \n \n' + q_string, TTS_URL)
        emit("chat-interface", '<TTS>')
        session['wait'] = 2
        print('CTX HISTORY:', ctx_msgs)

def get_target_word(srs):
    print('due before tomorrow words:', srs.get_due_before_date(tomorrow)) #TODO clean up
    target_word = srs.get_due_before_date(tomorrow)[0] if len(srs.get_due_before_date(tomorrow)) != 0 else list(srs.get_words())[0] #TODO better else statement 
    print('target word =', target_word) #TODO clean up
    return target_word

def learning_convo_sentence(prompt):
    s = session['learning-llm'].get_sentence(prompt)
    s_string = ''
    emit("chat-interface", '<START>')
    for tok in s:
        emit("chat-interface", tok)
        s_string += tok
    emit("chat-interface", '<END>')
    print('s_string:', s_string)
    return s_string

    tts_msgs[session['identity']] = generate_tts(s_string, TTS_URL)
    emit("chat-interface", '<TTS>')

    ctx_msgs[session['identity']] = f'A:\n{prompt}\n\nB:{s_string}'

def learning_convo_question(target_word):
    q = session['learning-llm'].get_question(target_word)
    q_string = ''
    emit("chat-interface", '<START>')
    for tok in q:
        emit("chat-interface", tok)
        q_string += tok
    emit("chat-interface", '<END>')
    print('q_string:', q_string)
    return q_string

    tts_msgs[session['identity']] = generate_tts(q_string, TTS_URL)
    emit("chat-interface", '<TTS>')

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
        print('grading incorrect word:', word) #TODO clean up
        srs.review_card(word, 'again')
    for word in correct:
        print('grading correct word:', word) #TODO clean up
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
def update_review_panel(srs):
    words_due = srs.get_due_before_date(tomorrow)
    string_words_due = ''
    for word in words_due:
        string_words_due = string_words_due + word + ' '
    print('string_words_due sent to main.js:', string_words_due) #TODO: clean up
    emit('srs-update', string_words_due)


print(f"Run this on your local machine in WSL or Git Bash:")
print(f"ssh -L {PORT}:{socket.gethostname()}:{PORT} {getpass.getuser()}@{socket.gethostname()}.hpc.msoe.edu")
app.run(host=socket.gethostname(), port=PORT, debug=False)
