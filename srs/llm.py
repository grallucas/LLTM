import os
import json
import getpass
from dataclasses import dataclass
from llama_cpp import Llama, LogitsProcessorList, LlamaGrammar

try: LLM_GLOBAL_INSTANCE
except NameError: LLM_GLOBAL_INSTANCE = None


TOKEN_COUNT_PATH = '/data/ai_club/team_3_2024-25/tokcounts/'
USER = getpass.getuser()

def inc_tok_count(mode, amt):
    fname = f'{USER}_{mode}.txt'
    try:
        with open(TOKEN_COUNT_PATH+fname, 'r') as f:
            count = int(f.read().strip())
    except FileNotFoundError:
        count = 0
    except ValueError:
        raise Exception(f'Token Count Corrupted: {fname}')
    
    count += amt

    with open(TOKEN_COUNT_PATH+fname, 'w') as f:
        f.write(str(count)+'\n')

# TODO: handle different model types
@dataclass
class Msg:
    role: str
    content: any

class LLM:
    _json_grammar = LlamaGrammar.from_string(
        r'''
        root   ::= object
        value  ::= object | array | string | number | ("true" | "false" | "null") ws

        object ::=
        "{" ws (
                    string ":" ws value
            ("," ws string ":" ws value)*
        )? "}" ws

        array  ::=
        "[" ws (
                    value
            ("," ws value)*
        )? "]" ws

        string ::=
        "\"" (
            [^"\\] |
            "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F]) # escapes
        )* "\"" ws

        number ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)? ws

        ws ::= [\n\t ]? # limit to 1 character
        ''',
        verbose=False
    )

    def __init__(self, system_prompt:str=None, verbose=0):
        global LLM_GLOBAL_INSTANCE
        if LLM_GLOBAL_INSTANCE is None:
            print('Initializing Global LLM Instance')
            LLM_GLOBAL_INSTANCE = Llama(
                n_ctx=4000,
                model_path='/data/ai_club/llms/llama-2-7b-chat.Q5_K_M.gguf',

                # n_ctx=8000,
                # model_path='/data/ai_club/llms/mistral-7b-instruct-v0.2.Q8_0.gguf',

                n_gpu_layers=-1, verbose=verbose,
                # embedding=True
            )
        self._hist = []
        self.reset(system_prompt)

    def reset(self, system_prompt:str=None):
        if system_prompt is not None:
            self._hist = [Msg('system', system_prompt)] # Init hist w/ sysprompt if a new one is given
        else:
            self._hist = self._main_hist[0:1] # Init hist w/ existing sysprompt (or empty hist) otherwise

        # NOTE: maybe a message can be added after the system prompt for some models (mistral 7b) which dont explicitly have a system prompt
        #   Assistant: "okay, I will respond to future messages accordingly"
            
    def get_pretty_hist(self) -> str:
        hist = ''
        for msg in self._hist:
            hist += f'{msg.role} --- {msg.content}\n__________\n\n'
        return hist

    def _hist_to_prompt(self, response_format):
        # TODO: this will handle the model-specific formatting stuff

        prompt = ''
        for msg in self._hist:
            if msg.role == 'system' or msg.role == 'user': prompt += f'[INST]{msg.content}[/INST]'
            elif msg.role == 'assistant': prompt += f'{msg.content}'

        if type(response_format) is dict:
            prompt += f'\n\n\nRespond in JSON using this format and absolutely nothing extra:\n{response_format}'

        return prompt

    def __call__(self, msg:str, response_format:str=None, **kwargs):
        '''
        response_format: None | dict | 'stream'
            None - output raw text
            dict - output JSON in the format of the supplied dict
            'stream' - output a generator of raw text
        '''
        self._hist.append(Msg('user', msg))
        prompt = self._hist_to_prompt(response_format)

        if response_format is None:
            raw = LLM_GLOBAL_INSTANCE(
                prompt,
                **kwargs
            )
            resp = raw['choices'][0]['text']

            inc_tok_count('in', raw['usage']['prompt_tokens'])
            inc_tok_count('out', raw['usage']['completion_tokens'])

            self._hist.append(Msg('assistant', resp))

            return resp
        elif type(response_format) is dict:
            raw = LLM_GLOBAL_INSTANCE(
                prompt,
                grammar = LLM._json_grammar,
                **kwargs
            )

            resp = json.loads(raw['choices'][0]['text'])

            inc_tok_count('in', raw['usage']['prompt_tokens'])
            inc_tok_count('out', raw['usage']['completion_tokens'])

            self._hist.append(Msg('assistant', resp))

            return resp
        elif response_format == 'stream':
            raise Exception('TODO')
        else:
            raise Exception(f'Unsupported Response Format: {response_format}')


    def tokenize(self, s:str):
        global LLM_GLOBAL_INSTANCE
        return LLM_GLOBAL_INSTANCE.tokenize(bytes(s, encoding='utf-8'), add_bos=False)

    def detokenize(self, toks:list[int]):
        global LLM_GLOBAL_INSTANCE
        return LLM_GLOBAL_INSTANCE.detokenize(toks).decode()