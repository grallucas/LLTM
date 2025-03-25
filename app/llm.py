from openai import OpenAI
import tiktoken
import getpass
import json
from dataclasses import dataclass
from copy import deepcopy
import threading

USER = getpass.getuser()

TOKEN_COUNT_PATH = None

client = OpenAI(
    base_url = "http://dh-dgxh100-2.hpc.msoe.edu:8000/v1",
    api_key = "not_used"
)

enc = tiktoken.get_encoding("cl100k_base")

def _ntoks(text):
    return enc.encode(text).__len__() + 4 # 4 extra tokens for llama: start_header, end_header, eos, 2 newlines (part of prompt format)

_tok_inc_lock = threading.Lock()

def _inc_tok_count(mode, amt):
    if TOKEN_COUNT_PATH is None:
        raise Exception('Set TOKEN_COUNT_PATH before infernece')
    fname = f'{USER}_{mode}.txt'
    with _tok_inc_lock:
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
    content: str
    response_format: list = None

class LLM:
    def __init__(self, sys_prompt:str=None):
        self._hist = []
        if sys_prompt:
            self._hist.append(Msg('system', sys_prompt))
            
        self._awaiting_streamed = False

    def save_state(self):
        return deepcopy(self._hist)

    def restore_state(self, state):
        self._hist = deepcopy(state)

    def _hist_to_prompt(self):
        prompt = []
        tok_count = 0
        for msg in self._hist:
            content = msg.content
            is_last = msg == self._hist[-1]
            is_fmted = type(msg.response_format) == list
            if is_fmted and is_last:
                json_format = {k:'...' for k in msg.response_format}
                content += f'\n\nRespond in this json: {json_format}'
            elif is_fmted:
                content += '\n\nRespond in JSON.'
            
            tok_count += _ntoks(content)

            prompt.append({
                'role': msg.role,
                'content': content
            })

        return prompt, tok_count

    def _call_default(self, messages, temperature, max_tokens):
        out = client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        out = out.choices[0].message.content
        out_toks = _ntoks(out)

        _inc_tok_count('out', out_toks)

        self._hist.append(Msg('assistant', out))

        return out
        
    def _call_stream(self, messages, temperature, max_tokens):
        out = client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        )

        self._hist.append(Msg('assistant', ''))
        self._awaiting_streamed = True

        def tok_stream():
            for t in out:
                tok = t.choices[0].delta.content

                if not tok: continue
                _inc_tok_count('out', 1)
                self._hist[-1].content += tok
                yield tok

            _inc_tok_count('out', 4) # 4 exta used in llama prompt format
            self._awaiting_streamed = False

        return tok_stream()

    def _call_fmted(self, messages, temperature, max_tokens, response_format):
        out = client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={'type': 'json_object'}   
        )
        out = out.choices[0].message.content
        out_toks = _ntoks(out)
        _inc_tok_count('out', out_toks)
        
        try:
            out = json.loads(out)
        except:
            raise Exception(f'Bad JSON output. {out} != {resposne_format}')

        if not all(k in out.keys() for k in response_format):
            raise Exception(f'Missing json keys. {out.keys()} != {response_format}')

        self._hist.append(Msg('assistant', f'{out}'))

        return out

    def __call__(self, prompt, response_format:str|list|None=None, temperature=0, max_tokens=1024):
        if self._awaiting_streamed:
            raise Exception('Cannot start a new message before ending a streamed one.')

        is_resp_fmted = type(response_format) is list

        self._hist.append(Msg('user', prompt))
        if is_resp_fmted:
            self._hist[-1].response_format = response_format

        messages, in_toks = self._hist_to_prompt()
        _inc_tok_count('in', in_toks)

        if response_format is None:
            return self._call_default(messages, temperature, max_tokens)
        elif response_format == 'stream':
            return self._call_stream(messages, temperature, max_tokens)
        elif is_resp_fmted:
            return self._call_fmted(messages, temperature, max_tokens, response_format)
        else:
            raise Exception(f'Unsupported Response Format: {response_format}')
