import os
import json
import getpass
from dataclasses import dataclass
from llama_cpp import Llama, LogitsProcessorList, LlamaGrammar

try: LLM_GLOBAL_INSTANCE
except NameError: LLM_GLOBAL_INSTANCE = None

TOKEN_COUNT_PATH = '/data/ai_club/team_3_2024-25/tokcounts/'
MODEL_PATH = os.getenv('MODEL_PATH')
N_CTX = int(os.getenv('N_CTX'))
USER = getpass.getuser()

def _inc_tok_count(mode, amt):
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

@dataclass
class Msg:
    role: str
    content: any
    response_format: dict = None

class LLM:
    # _json_grammar = LlamaGrammar.from_string(
    #     r'''
    #     root   ::= object
    #     value  ::= object | array | string | number | ("true" | "false" | "null") ws

    #     object ::=
    #     "{" ws (
    #                 string ":" ws value
    #         ("," ws string ":" ws value)*
    #     )? "}" ws

    #     array  ::=
    #     "[" ws (
    #                 value
    #         ("," ws value)*
    #     )? "]" ws

    #     string ::=
    #     "\"" (
    #         [^"\\] |
    #         "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F]) # escapes
    #     )* "\"" ws

    #     number ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)? ws

    #     ws ::= [\n\t ]? # limit to 1 character
    #     ''',
    #     verbose=False
    # )

    def __init__(self, system_prompt:str=None, verbose=0):
        global LLM_GLOBAL_INSTANCE
        if LLM_GLOBAL_INSTANCE is None:
            print('Initializing Global LLM Instance')
            LLM_GLOBAL_INSTANCE = Llama(
                n_ctx=N_CTX,
                model_path=MODEL_PATH,

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
            
    def get_pretty_hist(self) -> str:
        hist = ''
        for msg in self._hist:
            hist += f'{msg.role} --- {msg.content}\n__________\n\n'
        return hist

    def _hist_to_prompt(self, inject_resp=None):
        assert 'mixtral' in MODEL_PATH # TODO: this will handle model-specific formatting. For now it just works with Mixtral

        [sys_msg, *hist] = self._hist

        assert sys_msg.role == 'system' and sys_msg.response_format is None # First message must have role=system and response_format=None
        sys_prompt = [1, *LLM.tokenize(f'[INST] {sys_msg.content} [/INST] Understood.'), 2]

        remaining_prompt = ''
        for msg in self._hist[1:]:
            msg_content = msg.content

            is_last = msg == self._hist[-1]
            has_fmt = not not msg.response_format
            if has_fmt and is_last:
                msg_content += f'\n\n\nRespond in JSON with this format: {msg.response_format}'
            if has_fmt and not is_last:
                msg_content += '\n\n\nRespond in JSON.'

            assert msg.role != 'system' # System message can only be first

            if msg.role == 'user': remaining_prompt += f' [INST] {msg_content} [/INST] ' + ((inject_resp if is_last else None) or '')
            elif msg.role == 'assistant': remaining_prompt += f'{msg_content}'
        remaining_prompt = LLM.tokenize(remaining_prompt)

        return sys_prompt + remaining_prompt

    def __call__(self, msg:str, response_format:str|dict=None, **kwargs):
        '''
        response_format: None | dict | 'stream'
            None - output raw text
            dict - output JSON in the format of the supplied dict
            'stream' - output a generator of raw text
        '''
        self._hist.append(Msg('user', msg, (response_format if type(response_format) is dict else None)))
        prompt = self._hist_to_prompt()
        _inc_tok_count('in', len(prompt))

        if response_format is None:
            raw = LLM_GLOBAL_INSTANCE(
                prompt,
                **kwargs
            )
            
            resp = raw['choices'][0]['text']
            _inc_tok_count('out', raw['usage']['completion_tokens'])
            self._hist.append(Msg('assistant', resp))

            return resp
        elif type(response_format) is dict:
            assert 0 # TODO
        elif response_format == 'stream':
            raw = LLM_GLOBAL_INSTANCE(
                prompt,
                stream = True,
                **kwargs,
            )

            self._hist.append(Msg('assistant', ''))
            msg = self._hist[-1]
            
            def tok_stream():
                for tok in raw:
                    tok = tok['choices'][0]['text']
                    _inc_tok_count('out', 1)
                    msg.content += tok
                    yield tok

            return tok_stream()
        else:
            raise Exception(f'Unsupported Response Format: {response_format}')


        # if response_format is None:
        #     raw = LLM_GLOBAL_INSTANCE(
        #         prompt,
        #         **kwargs
        #     )
        #     resp = raw['choices'][0]['text']

        #     _inc_tok_count('out', raw['usage']['completion_tokens'])

        #     self._hist.append(Msg('assistant', resp))

        #     return resp
        # elif type(response_format) is dict:
        #     raw = LLM_GLOBAL_INSTANCE(
        #         prompt,
        #         grammar = LLM._json_grammar,
        #         **kwargs
        #     )

        #     try:
        #         resp = json.loads(raw['choices'][0]['text'])
        #     except json.JSONDecodeError:
        #         raise Exception(f"Couldn't Decode Json:\n{raw['choices'][0]['text']}")


        #     _inc_tok_count('out', raw['usage']['completion_tokens'])

        #     self._hist.append(Msg('assistant', resp))

        #     return resp
        # elif response_format == 'stream':
        #     raw = LLM_GLOBAL_INSTANCE(
        #         prompt,
        #         stream = True,
        #         **kwargs,
        #     )

        #     self._hist.append(Msg('assistant', ''))
        #     msg = self._hist[-1]

        #     def tok_stream():
        #         for tok in raw:
        #             tok = tok['choices'][0]['text']
        #             _inc_tok_count('out', 1)
        #             msg.content += tok
        #             yield tok

        #     return tok_stream()
        # else:
        #     raise Exception(f'Unsupported Response Format: {response_format}')


    def tokenize(s:str, add_bos=False):
        global LLM_GLOBAL_INSTANCE
        return LLM_GLOBAL_INSTANCE.tokenize(bytes(s, encoding='utf-8'), add_bos=add_bos)

    def detokenize(toks:list[int]):
        global LLM_GLOBAL_INSTANCE
        return LLM_GLOBAL_INSTANCE.detokenize(toks).decode()