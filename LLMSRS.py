from SRS import SRS
import llm as L
from llama_cpp import Llama
import re

class LLMSRS:
    srs = SRS()
    chat_llm = L.LLM('You are language chatbot. You speak using low-level, easy to comprehend words. You end every sentence with a short quiz to see if they understand')
    grader_llm = L.LLM('You grade the responses of a user input and flag the words that are used incorrectly')
    all_mistakes = {}

    def graded_response(self, user_input : str) -> str:
        resp = self.get_response(user_input)
        # mistakes_dictionary = self.get_errors(user_input)
        # all_mistakes.append(mistakes_dictionary)
        # for word in mistakes_dictionary.keys():
        #     SRS.review_card(word, 'again')
        return resp


    def get_response(self, user_input : str) -> str:
        resp = self.chat_llm(user_input, max_tokens=200, logits_processor=[self.logits_processor])
        return resp

    #TODO: results in JSONDecodeError (due to dictionary format?)
    def get_errors(self, user_input : str) -> dict[str, str]: # {'word':'reason'}
        mistakes_dictionary = {'word':'reason'}
        mistakes = self.grader_llm(user_input, mistakes_dictionary)
        # grader_llm.get_pretty_hist() # print output for debugging
        return mistakes

    def logits_processor(self, prev_tok_ids, next_tok_logits):
        
        # print(prev_tok_ids, next_tok_logits)

        next_tok_logits[995] -= 1000
    
        return next_tok_logits

if __name__ == '__main__':
    llm = LLMSRS()
    print(llm.graded_response("hello"))
