import json
import re

# IMPORTANT NOTE:
#   for future updates of this code, the formatted response generation would ideally be be refactored into a class with instance vars:
#       self.prompt, self.LLM_INSTANCE, self.verbose, etc.
#   These vars are currently being passed via func args.

class Repr:
    def __init__(self, s): self.s = s
    def __str__(self): return self.s
    def __repr__(self): return self.s

FORMAT_PROMPT = 'Respond in JSON with this format, writing strings with double quotes and numbers with JS notation (commas end rather than separate digits)'

def pretty_response_format_rec(response_format):
    if response_format in [str, int, float]:
        return Repr(response_format.__name__)
    elif type(response_format) == dict:
        return {
            Repr(f'"{k}"'): pretty_response_format_rec(v)
            for k,v in response_format.items()
        }
    elif type(response_format) == list:
        sub, etc = response_format

        if etc == ...:
            return [pretty_response_format_rec(sub), Repr('...')]
        elif type(etc) is int:
            return [pretty_response_format_rec(sub), Repr(f'{etc} total...')]

        else:
            raise Exception(f'List size must be int or `...`, but found: {etc}')

    else:
        raise Exception(f'Unsupported value type: {v}')

def pretty_response_format(response_format):
    return f'{FORMAT_PROMPT}: {pretty_response_format_rec(response_format)}'

def gen_response_formated_rec(LLM_GLOBAL_INSTANCE, response_format, prompt_ref, temperature, max_tokens, verbose):
    if verbose:
        gen_start_idx = len(prompt_ref[0])
        print(f'Generating {response_format}')
    if response_format == str:
        prompt_ref[0] += '"'
        s = LLM_GLOBAL_INSTANCE(
            prompt_ref[0],
            max_tokens=max_tokens, temperature=temperature,
            stream=True,
            # grammar=str_grammar
        )
        for t in s:
            t = t['choices'][0]['text']
            str_end = re.search(r'(^|[^\\])(")', t)
            if str_end:
                prompt_ref[0] += t[:str_end.span(2)[0]]
                break
            prompt_ref[0] += t
        prompt_ref[0] += '"'

    elif response_format in [float, int]:
        s = LLM_GLOBAL_INSTANCE(
            prompt_ref[0],
            max_tokens=max_tokens, temperature=temperature,
            stream=True,
            # grammar=num_grammar
        )
        for t in s:
            t = t['choices'][0]['text']
            str_end = re.search(r'[,}]', t)
            if str_end:
                prompt_ref[0] += t[:str_end.span()[0]]
                break
            prompt_ref[0] += t

    elif type(response_format) == dict:
        prompt_ref[0] += '{'
        first = True
        for k,v in response_format.items():
            if not first: prompt_ref[0] += ', '
            first = False
            prompt_ref[0] += f'"{k}": '
            gen_response_formated_rec(LLM_GLOBAL_INSTANCE, v, prompt_ref, temperature, max_tokens, verbose)
        prompt_ref[0] += '}'

    elif type(response_format) == list:
        sub_type, etc = response_format

        i = None
        if type(etc) is int:
            i = etc
        else:
            assert etc == ...

        prompt_ref[0] += '['
        while True:
            if not i is None:
                if i == 0: break
                i -= 1

            gen_response_formated_rec(LLM_GLOBAL_INSTANCE, sub_type, prompt_ref, temperature, max_tokens, verbose)

            has_target_size = not i is None
            if has_target_size:
                if i>0:
                    prompt_ref[0] += ', '
            else:
                # get the next non-space token.
                next_tok = ''
                cutoff = len(prompt_ref[0])
                while not next_tok.strip():
                    next_tok = LLM_GLOBAL_INSTANCE(
                        prompt_ref[0],
                        max_tokens=1, temperature=0,
                        stream=False,
                    )['choices'][0]['text']
                    prompt_ref[0] += next_tok
                prompt_ref[0] = prompt_ref[0][:cutoff] # dont include all the generated space in the prompt

                if ']' in next_tok:
                    break
                elif ',' in next_tok:
                    prompt_ref[0] += ', '
                    continue
                else:
                    raise Exception(f'Theoretically unreachable err: invalid list next tok: "{next_tok}"')

        prompt_ref[0] += ']'

    else:
        raise Exception(f'Unexpected type for response format: {response_format}')

    if verbose:
        print(f'Generated: {prompt_ref[0][gen_start_idx:]}')

def gen_response_formated(LLM_GLOBAL_INSTANCE, response_format, prompt, temperature, max_tokens, verbose):
    assert FORMAT_PROMPT in prompt
    json_start = len(prompt)
    prompt_ref = [prompt]
    gen_response_formated_rec(LLM_GLOBAL_INSTANCE, response_format, prompt_ref, temperature, max_tokens, verbose)
    return prompt_ref[0][json_start:]
