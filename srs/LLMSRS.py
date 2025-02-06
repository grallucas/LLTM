from SRS import SRS
import llm as L
from llama_cpp import Llama
import re

class LLMSRS:
    srs = SRS()
    chat_llm = L.LLM('You are language chatbot. You speak using low-level, easy to comprehend words. You end every sentence with a short quiz to see if they understand')
    grader_llm = L.LLM("you are a language teacher grading the response of a user in a conversation. Using a Python dictionary, give me the incorrect words and their reasoning from the user.")
    all_mistakes = {}

    def graded_response(self, user_input : str) -> str:
        resp = self.get_response(user_input)
        mistakes_dictionary = self.get_errors(user_input)
        self.all_mistakes.update(mistakes_dictionary)
        for word in mistakes_dictionary.keys():
            self.srs.review_card(word, 'again')
        return resp


    def get_response(self, user_input : str) -> str:
        resp = self.chat_llm(user_input, max_tokens=200, logits_processor=[self.logits_processor])
        return resp

    #TODO: results in JSONDecodeError (due to dictionary format?)
    def get_errors(self, user_input : str) -> dict[str, str]: # {'word':'reason'}
        mistakes_dictionary = {'words': 'list of ["word1", ...]', 'reasons': 'list of ["reason1", ...]'}
        mistakes = self.grader_llm(user_input, mistakes_dictionary, max_tokens=1000)
        # grader_llm.get_pretty_hist() # print output for debugging
        return mistakes

    def logits_processor(self, prev_tok_ids, next_tok_logits):
        
        # print(prev_tok_ids, next_tok_logits)

        next_tok_logits[995] -= 1000
    
        return next_tok_logits

if __name__ == '__main__':
    from datetime import datetime, timezone
    llm = LLMSRS()
    print(llm.graded_response("Hi! This is my response. I'm typing back to you wiht some erors in here. "))
    now = datetime.now(timezone.utc)
    print(llm.graded_response("Hi! This is my response. I'm typing back to you wiht some erors in here. I thik its going to be a great day today! The sun is shining and i can’t wait to get out and enjoy the weather. Hope you hav a good time too!"))
    print(llm.srs.get_due_before_date(now))
    print(llm.all_mistakes)
