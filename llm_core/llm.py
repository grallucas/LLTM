import os
import json
import getpass
from dataclasses import dataclass
from llama_cpp import Llama, LogitsProcessorList, LlamaGrammar
import llm_core.response_format as response_fmt
import threading

llm_lock = threading.Lock()

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
            self._hist = self._hist[0:1] # Init hist w/ existing sysprompt (or empty hist) otherwise
            
    def get_pretty_hist(self) -> str:
        hist = ''
        for msg in self._hist:
            hist += f'{msg.role} --- {msg.content}\n__________\n\n'
        return hist

    def _hist_to_prompt_mixtral(self, inject_resp):
        [sys_msg, *hist] = self._hist

        assert sys_msg.role == 'system' and sys_msg.response_format is None # First message must have role=system and response_format=None
        sys_prompt = [1, *LLM.tokenize(f'[INST] {sys_msg.content} [/INST] Understood.'), 2]

        remaining_prompt = ''
        for msg in self._hist[1:]:
            msg_content = msg.content
            is_last = msg == self._hist[-1]
            has_fmt = not not msg.response_format
            if has_fmt and is_last:
                msg_content += f'\n\n\n{response_fmt.pretty_response_format(msg.response_format)}'
            if has_fmt and not is_last:
                msg_content += '\n\n\nRespond in JSON.'

            assert msg.role != 'system' # System message can only be first

            if msg.role == 'user': remaining_prompt += f' [INST] {msg_content} [/INST] ' + ((inject_resp if is_last else None) or '')
            elif msg.role == 'assistant': remaining_prompt += f'{msg_content}'
        remaining_prompt = LLM.tokenize(remaining_prompt)

        return sys_prompt + remaining_prompt

    def _hist_to_prompt_qwen(self, inject_resp):
        prompt = []

        for msg in self._hist:
            msg_content = msg.content
            is_last = msg == self._hist[-1]
            has_fmt = not not msg.response_format
            if has_fmt and is_last:
                msg_content += f'\n\n\n{response_fmt.pretty_response_format(msg.response_format)}'
            if has_fmt and not is_last:
                msg_content += '\n\n\nRespond in JSON.'

            newline_if_has_next = (b'' if is_last else b'\n')
            prompt += [
                *LLM_GLOBAL_INSTANCE.tokenize(b'<|im_start|>' + bytes(msg.role, encoding='utf-8') + b'\n', special=True),
                *LLM_GLOBAL_INSTANCE.tokenize(bytes(msg_content, encoding='utf-8'), special=False),
                *LLM_GLOBAL_INSTANCE.tokenize(b'<|im_end|>' + newline_if_has_next, special=True)
            ]

            if is_last and msg.role == 'user':
                prompt += [
                    *LLM_GLOBAL_INSTANCE.tokenize(b'\n<|im_start|>assistant\n' + bytes(inject_resp or '', encoding='utf-8'), special=True)
                ]

        return prompt

    def _hist_to_prompt(self, inject_resp=None):
        if 'mixtral' in MODEL_PATH: return self._hist_to_prompt_mixtral(inject_resp)
        if 'qwen' in MODEL_PATH: return self._hist_to_prompt_qwen(inject_resp)
        raise Exception('Model type not supported')

    def __call__(self, msg:str, response_format:str|dict=None, temperature=0, max_tokens=100, verbose=False, **kwargs):
        '''
        response_format: None | dict | list | type(float) | type(int) | type(str) | 'stream'
            None - output raw text
            'stream' - output a generator of raw text
            response_format - see below
            temperature - randomness of model output
            max_tokens - max tokens of output
            verbose - whether to print value generation info for response_format
            
            This function supports arbitrary structued output supplied in `response_format` via a data structure consisting of nested dicts, lists, ints, floats, and str.
            When supplying a list, supply it in the format [TYPE, COUNT or `...`].
            For instance:
                msg = "What is one capital city in Europe?"
                response_format = {'country': str, 'capital': str, 'pop': int, 'nearest_cities': [{'name': str, 'pop': int}, 3]}
            This example generates one capital along with a list of 3 cities, populations included for all cities.
            The following would work for an arbitrarily-large list of nearest cities:
                {'country': str, 'capital': str, 'pop': int, 'nearest_cities': [{'name': sinastr, 'pop': int}, ...]}
            
            Note: in the case of formatted responses, max tokens is the highest number of output tokens PER JSON VALUE.

            RECOMMENDED for formatted responses:
                temperature = 0
                max_tokens = <some sufficiently LARGE number, e.g., 1000>
        '''
        with llm_lock:
            response_format_is_special = type(response_format) in [list, dict] or response_format in [float, int, str]
            if response_format_is_special and (not type(response_format) is dict):
                assert 0 # It's possible to have a non-dict response_format with grammars, but this remains unimplemented 

            self._hist.append(Msg('user', msg, (response_format if response_format_is_special else None)))
            prompt = self._hist_to_prompt()
            _inc_tok_count('in', len(prompt))

            if response_format is None:
                print('GENERATE', msg)
                raw = LLM_GLOBAL_INSTANCE(
                    prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                print('-- generated --')

                resp = raw['choices'][0]['text']
                _inc_tok_count('out', raw['usage']['completion_tokens'])
                self._hist.append(Msg('assistant', resp))

                return resp
            elif response_format_is_special:
                # TODO: reimplement formatted generation to work with tokens instead of text.
                # ... b/c currently, any special token strings in the message content will be parsed  

                prompt = LLM_GLOBAL_INSTANCE.detokenize(prompt, special=True).decode()
                resp = response_fmt.gen_response_formated(LLM_GLOBAL_INSTANCE, response_format, prompt, temperature, max_tokens, verbose)
                
                try:
                    self._hist.append(Msg('assistant', resp))
                    return json.loads(resp)
                except json.JSONDecodeError as e:
                    raise Exception(f'Cannot parse this JSON: {resp}')
            elif response_format == 'stream':
                raw = LLM_GLOBAL_INSTANCE(
                    prompt,
                    stream=True,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
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

    def tokenize(s:str, add_bos=False):
        global LLM_GLOBAL_INSTANCE
        return LLM_GLOBAL_INSTANCE.tokenize(bytes(s, encoding='utf-8'), add_bos=add_bos)

    def detokenize(toks:list[int]):
        global LLM_GLOBAL_INSTANCE
        return LLM_GLOBAL_INSTANCE.detokenize(toks).decode()