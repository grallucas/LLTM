import importlib
import sys
import llm as L
import os
import random

"""
Class for the introductory converstaions with Rose
following a more conversation pattern, intended to 
be used for reviewing known words.

Pattern:
    Q in english (or target language if enough vocab)
    User answers with words to review
    User makes a new sentence with words to review
    LLM responds with known words
    repeat
"""

class learning_llm:
    def __init__(self, vocab, language):
        self.language = language
        # self.sentence_llm = L.LLM("You are a helpfull assistant. "
        #                           f"You respond using simple sentences in {language}")

        self.question_llm = L.LLM('Tell the user that SOMETHING HAS GONE WRONG')
        self.update_prompt_vocab(vocab)

        self.translate_llm = L.LLM(f"You are a helpful assistant. You translate {language} words into English.")
        self.eval_llm = L.LLM("You are a helpful assistant. "
                 f"You are given questions and answers to sentences in {language} and determine if they are correct."
                 "Speak directly to the user.")
    
    def update_prompt_vocab(self, vocab):
        self.question_llm._hist[0].content = (
            f'You are a {self.language} language teacher named Rossi. '
            f'\nUse lots of emojis. All of your responses must be grammatically correct {self.language}.'
            f'\n\nIMPORTANT: Your responses must only use words in this allowed vocab: {vocab} and any emoji/punctuation.'
        )

    def get_sentence(self, prompt):
        s = self.question_llm(
            f"Respond to the prompt \"{prompt}\" in an engaging way using only the allowed vocab.",
            response_format='stream',
            max_tokens=None,
            temperature=0.1,
            # verbose=False
        )
        return s
    
    def get_question(self, target_word):
        prompt = f'Use only the allowed vocabulary to write a NEW question for which a reply can include the target word: "{target_word}"'
        if target_word == 'ciao':
            prompt = 'Use only the allowed vocabulary, and simply ask the user to introduce themself "Ciao! Io sono Rossi. Tu?"'
        print('q prompt:', prompt)
        q = self.question_llm(
            prompt,
            response_format='stream',
            max_tokens=None,
            temperature=0.1,
            # verbose=False
        )
        return q
    
    # not used
    def get_answer(self, target_word):
        answer = self.question_llm(
            f"Translate the following {self.language} word into English. Respond with only the answer."
            f"Word: {target_word}",
            max_tokens=None,
            temperature=0.1,
            # verbose=False
        )
        return answer
    
    # not used
    def evaluate(self, sentence, question, correct_answer, user_answer):
        evaluation = self.eval_llm(
            "Explain in English if the following answer was correct: "
             f"Sentence: {sentence}, question: {question}, correct answer: {correct_answer}, user answer: {user_answer}",
            response_format='stream',
            max_tokens=None,
            temperature=0.1,
            # verbose=False
        )
        return evaluation
    
    # not used
    def grade(self):
        grade = self.eval_llm(
            "Yes or no, was the answer correct? Respond with only 'yes' or 'no.",
            max_tokens=None,
            temperature=0.1,
            # verbose=False
        )
        return grade


def main():
    vocab = get_vocab_qs()
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

def get_vocab_qs(): ### This is kind of like jeopardy. Maybe we can take advantage of that? TODO ###
    vocab = {'koira': [
        {'s' : 'Tama on minun koirana.', 'q' : 'What is Mine?'}
    ], 'talo' : [
        {'s' : 'Talo on pieni.', 'q' : 'What is small?'}
    ]
    }
    return vocab

if __name__ == "__main__":
    main()