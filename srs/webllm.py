from SRS import SRS
import llm as L
from llama_cpp import Llama
import re

def run_llm(args):
    user_input = args[1]
    resp = chat_llm(user_input, max_tokens=200, logits_processor=[logits_processor])
    return resp

def logits_processor(prev_tok_ids, next_tok_logits):
    
    # print(prev_tok_ids, next_tok_logits)

    next_tok_logits[995] -= 1000
 
    return next_tok_logits

if __name__ == '__main__':
    srs = SRS()
    chat_llm = L.LLM('You are language chatbot. You speak using low-level, easy to comprehend words. You end every sentence with a short quiz to see if they understand')

    print(run_llm(sys.argv[1:]))