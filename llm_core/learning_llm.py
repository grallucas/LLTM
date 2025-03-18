import importlib
import sys
import llm as L
import os

"""
Class for the introductory converstaions with Rose
Users aren't expected to know many words, instead being
quizzed in their native language on new target language words
"""
class learning_llm:
    def __init__(self, language):
        self.language = language
        self.sentence_llm = L.LLM("You are a helpful language learning assistant. You respond using words from your dictionary "
                     f"to create simple sentences in {language}. ")
        self.question_llm = L.LLM("You are a helpful language learning assistant. You ask users questions in English "
                     f"about sentences in {language} to test if they understand the meaning. "
                     "For example, in the sentence \"Koira juoksee puistossa.\", and intelligent question would be \"What is the subject doing?\" or \"What is the subject?\". "
                    )
        self.eval_llm = L.LLM("You are a helpful language learning assistant. "
                 f"You are given questions and answers to sentences in {language} and determine if they are correct.")
    
    def get_sentence(self, words):
        sentence = self.sentence_llm(
            f"Select a word from {self.language} and write a simple sentence using it. "
            "The sentence MUST contain a subject, verb, and object. "
            ,
            response_format='stream',
            max_tokens=None,
            temperature=0.1,
            verbose=False
        )
        return sentence
    
    def get_question(self, input_sentence):
        question = self.question_llm(
            "Write a simple question in English about a word in the following sentence to see if "
            f"the user understands: {input_sentence}",
            response_format='stream',
            max_tokens=None,
            temperature=0.1,
            verbose=False
        )
        return question
    
    def get_answer(self):
        answer = self.question_llm(
            "Write the answer in English about the quesiton you made.",
            response_format={'Answer':str},
            max_tokens=None,
            temperature=0.1,
            verbose=False
        )
        return answer
    
    def test(self, n, words):
        sentence = self.get_sentence(3, words, self.language)
        print(sentence)
        question = self.get_question2(sentence, self.language)
        print(question)
        return (sentence, question)
    
    def evaluate(self, sentence, question, correct_answer, user_answer):
        evaluation = self.eval_llm(
            "Explain in English if the following answer was correct: "
             f"Sentence: {sentence}, question: {question}, correct answer: {correct_answer}, user answer: {user_answer}",
            response_format='stream',
            max_tokens=None,
            temperature=0.1,
            verbose=False
        )
        print(self.eval_llm.get_pretty_hist())
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
    finnish_words = get_finnish_words()
    learn = learning_llm('Finnish')
    sentence = learn.get_sentence(1, finnish_words)
    print(sentence)
    question = learn.get_question(sentence)
    print(question)
    user_answer = input("Enter your answer: ")
    #evaluation = learn.evaluate(sentence, question, question['Answer'], user_answer)
    #print(evaluation)

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