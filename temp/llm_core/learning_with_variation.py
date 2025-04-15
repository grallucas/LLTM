import importlib
import sys
sys.path.append("./llm_core")
import llm as L
import os
import random
"""
Class for the introductory converstaions with Rose
Users aren't expected to know many words, instead being
quizzed in their native language on new target language words

Asks and evaluates questions based on hard-coded examples
Vocab is a dictionary with target-language vocab words as keys
and lists of example sentence-question pairs as the values.
Ex: vocab = {
    'koira' : [
        {'S': 'Tama on minun koirana', 'Q': 'What is Mine?'},
        {'S': '... koira', 'Q': '...?'},
        ...
    ],
    'talo' : [
        ...
    ],
    ...
    }

The intended flow of this learning class is as follows:
     - vocab word is selected from SRS as either review or a new word
     - random sentence-question pair for the word is grabbed from vocab (dict)
     - the sentence is given to a monolingual llm to make a variation of
     - the variation and originally linked question are given to a billingual 
       llm for a relevant question, similar to the original
     - The answer is the target vocab word, but the user will answer in their 
       native language, so the vocab word is translated (how? TODO)
     - The sentence and question are shown to the user, and the response is 
       evaluated by another llm
     - SRS is updated (TODO)
"""
class learning_llm:
    def __init__(self, vocab, language='Finnish'):
        self.language = language
        self.vocab = vocab
        self.sentence_llm = L.LLM("You are a helpful assistant. You take a given sentence "
                     f"with a target word and make a similar variation of it. Keep the target word the same.")
        self.question_llm = L.LLM("You are a helpful assistant. You will be given a sentence and question pair for "
                     f"a target vocab word in {language}. A varation of the sentence will be given to you; your goal "
                     "is to make a similar variation of the question while keeping the answer as the taget vocab word."
                     "For example, in the sentence \"Koira juoksee puistossa.\", and intelligent question would be \"What is the subject doing?\" or \"What is the subject?\". "
                    )
        self.translate_llm = L.LLM(f"You are a helpful assistant. You translate {language} words into English.")
        self.eval_llm = L.LLM("You are a helpful assistant. "
                 f"You are given questions and answers to sentences in {language} and determine if they are correct."
                 "Speak directly to the user.")
    
    def get_sentence(self, target_word):
        if target_word in self.vocab:
            sentences = self.vocab[target_word]
            s = sentences[random.randint(0, len(sentences) - 1)]['s']
            s_variation = self.sentence_llm(
                f"Given the target word '{target_word}' for the sentence {s}, create "
                "a creative, gramatically correct variation of it that keeps the target word the same. "
                "Respond with only the sentence.",
                response_format='stream',
                max_tokens=None,
                temperature=0.1,
                verbose=False
                )
            return (s, s_variation)
        else:
            print("Error: target word not found for sentence creation.")
    
    def get_question(self, target_word, s, s_variation):
        if target_word in self.vocab:
            questions = self.vocab[target_word]
            q = questions[random.randint(0, len(questions) - 1)]['q']
            q_variation = self.question_llm(
                f"The target word  is '{target_word}'. The sentence-question pair is '{s}', '{q}'. "
                f"The variation of the sentence is '{s_variation}'. Create an English question related to the "
                "sentence variation while maintaining the style of the original quesiton pair. "
                "Respond with only the question.",
                response_format='stream',
                max_tokens=None,
                temperature=0.1,
                verbose=False
                )
            return q_variation
        else:
            print("Error: target word not found for question creation.")
    
    def get_answer(self, target_word):
        answer = self.question_llm(
            f"Translate the following {self.language} word into English. Respond with only the answer."
            f"Word: {target_word}",
            response_format={'Answer':str},
            max_tokens=None,
            temperature=0.1,
            verbose=False
        )
        return answer
    
    def evaluate(self, sentence, question, correct_answer, user_answer):
        evaluation = self.eval_llm(
            "Explain in English if the following answer was correct: "
             f"Sentence: {sentence}, question: {question}, correct answer: {correct_answer}, user answer: {user_answer}",
            response_format='stream',
            max_tokens=None,
            temperature=0.1,
            verbose=False
        )
        return evaluation
    
    def grade(self):
        grade = self.eval_llm(
            "Yes or no, was the answer correct?", # bool response formats do not work
            response_format={'correct' : str},
            max_tokens=None,
            temperature=0.1,
            verbose=False
        )
        return grade


def main():
    vocab = get_vocab()
    learn = learning_llm(vocab)
    s, sentence = learn.get_sentence('koira')
    s_string = ''
    for tok in sentence: 
        s_string = s_string + str(tok)
    print(s_string)
    question = learn.get_question('koira', s, s_string)
    q_string = ''
    for tok in question: 
        q_string = q_string + str(tok)
    print(q_string)
    answer = learn.get_answer('koira')
    print(answer)
    user_answer = input("enter your answer: ")
    evaluation = learn.evaluate(s_string, q_string, answer, user_answer)
    e_string = ''
    for tok in evaluation: 
        e_string = e_string + str(tok)
    print(e_string)

def get_vocab(): ### This is kind of like jeopardy. Maybe we can take advantage of that? TODO ###
    vocab = {'koira': [
        {'s' : 'Tama on minun koirana.', 'q' : 'What is Mine?'}
    ], 'talo' : [
        {'s' : 'Talo on pieni.', 'q' : 'What is small?'}
    ]
    }
    return vocab

def get_finnish_words():
    TEACHER_NAME = 'Rose' # localized to target language (regular 'e' for Finnish)
    LEARNER_NAME = 'Lucas' # obtained from user profile

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

    finnish_words = ""
    for i in range(len(allowed_vocab)):
        finnish_words = finnish_words + allowed_vocab[i]
    return finnish_words

if __name__ == "__main__":
    main()