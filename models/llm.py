import torch
import torch.nn as nn
# from torch.distributions import Categorical
import transformers
from transformers import AutoModelForCausalLM, AutoConfig, BitsAndBytesConfig
import gc
import emoji

class IMDecoderLayer(nn.Module):
    mask = None
    vspace_to_emb = None
    block_strength = []

    def __init__(self, original_layer, vspace_to_emb, config, block_idx):
        super().__init__()
        self.original_layer = original_layer

        if IMDecoderLayer.vspace_to_emb == None:
            IMDecoderLayer.vspace_to_emb = vspace_to_emb.weight

        common_dtype = IMDecoderLayer.vspace_to_emb.dtype

        self.block_idx = len(IMDecoderLayer.block_strength)
        IMDecoderLayer.block_strength.append(
            nn.Parameter(torch.tensor(1.0, dtype=common_dtype).to('cuda:1'))
        )

        self.vstate = torch.zeros(config.vocab_size, dtype=common_dtype).to('cuda:1')

    def forward(self, hidden_states, *args, **kwargs):
        hidden_states = self.original_layer(hidden_states, *args, **kwargs)
        hidden_states = hidden_states[0]

        mask = IMDecoderLayer.mask
        assert mask != None
        if mask:
            n_allowed = len(mask)
            n_disallowed = self.vstate.shape[-1] - n_allowed

            self.vstate[:] = -1/n_disallowed
            self.vstate[mask] = 1/n_allowed
            
            hidden_states[-1,-1,:] += (self.vstate @ IMDecoderLayer.vspace_to_emb) * IMDecoderLayer.block_strength[self.block_idx]

        return (hidden_states,)
        
for i, s in enumerate(IMDecoderLayer.block_strength):
    c = 2 # This is a hyperparameter - "mask strength"
    s.data.fill_(c*i/(i+c))

# MODEL_NAME = 'meta-llama/Llama-3.1-8B-Instruct'
MODEL_NAME = '/data/ai_club/team_3_2024-25/llama3.1/snapshots/0e9e39f249a16976918f6564b8830bc894c89659/'

config = AutoConfig.from_pretrained(MODEL_NAME)

tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_NAME)
if tokenizer.pad_token is None:
    tokenizer.add_special_tokens({'pad_token': '[PAD]'})

bnb = BitsAndBytesConfig(
    load_in_8bit=True,
    # bnb_8bit_use_double_quant=True,
    # bnb_8bit_quant_type="nf8",
    # bnb_8bit_compute_dtype=torch.bfloat16,

    llm_int8_enable_fp32_cpu_offload=True
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    low_cpu_mem_usage=True,
    # attn_implementation="flash_attention_2",
    # torch_dtype=torch.bfloat16,
    quantization_config=bnb
)

# FREEZE existing model.
for param in model.parameters():
    param.requires_grad = False

# REPLACE transformer blocks with IM ones
for i, _ in enumerate(model.model.layers):
    model.model.layers[i] = IMDecoderLayer(model.model.layers[i], model.model.embed_tokens, config, i)

# def tokenize(batch):
#         tokens = tokenizer(batch, return_tensors='pt', padding=True)
#         tokens = {k:v.to('cuda') for k,v in tokens.items()}
#         return tokens

def tokof(s, check=True):
    toks = tokenizer(s, add_special_tokens=False)['input_ids']
    if check:
        if len(toks) > 1: raise Exception(f'This is more than one tok: {toks}')
        return toks[0]
    return toks

# --- vocab ---

vocab_raw = []
trie = {}

def get_next_allowed(given, trie):
    allowed = trie
    for tok in given:
        if tok in allowed:
            allowed = allowed[tok]
        elif None in allowed and tok in trie:
            allowed = trie[tok]
        else:
            # NOTE: fix for invalid prior seq - just pretend we're starting a new word
            given = ['.'] 
            allowed = trie

    allowed = list(allowed.keys())

    if None in allowed and given:
        allowed += [t for t in trie.keys()]

    allowed = [v for v in allowed if v]

    return allowed

def stream_response(messages):
    print('vocab_raw', vocab_raw)
    assert vocab_raw[0] in messages[0] # message should have all vocab. Only checking first is good enough for now

    tokens = tokenizer.encode(f'<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{messages[0]}<|eot_id|>', add_special_tokens=False)
    for i, m in enumerate(messages[1:]):
        role = 'user' if i%2==0 else 'assistant'
        tokens += tokenizer.encode(f'<|start_header_id|>{role}<|end_header_id|>\n\n{m}<|eot_id|>', add_special_tokens=False)
    tokens += tokenizer.encode('<|start_header_id|>assistant<|end_header_id|>\n', add_special_tokens=False)

    print(tokenizer.decode(tokens)) # for debug

    # Spam the GC
    for _ in range(10):
        if gc.collect() == 0:
            break
    torch.cuda.empty_cache() 

    def next_tok(use_mask):
        allowed = get_next_allowed(tokens, trie) + [tokof('<|eot_id|>')]

        if use_mask:
            IMDecoderLayer.mask = allowed
        else:
            IMDecoderLayer.mask = []
        
        logits = model(torch.tensor([tokens]).to('cuda:1')).logits[0][-1]

        logits[allowed] += 100
        # Categorical(logits=logits).sample()
        tok_id = int(logits.argmax())

        if all(t == tokens[-1] for t in  tokens[-5:]):
            tok_id = tokof('<|eot_id|>')

        tokens.append(tok_id)
        return tok_id

    use_mask = True
    while True:
        try:
            tok_id = next_tok(use_mask)
            if tok_id == tokof('<|eot_id|>'): break
            yield tokenizer.decode(tok_id)
        except Exception as e:
            if use_mask == False:
                print('LLM is OOM, but already not using mask')
                raise
            print('<<Temporarily stopping mask>>')
            use_mask = False

    yield '<END>'

# --- server :( ---

import asyncio
import websockets
import socket
import sys
import io

PORT = sys.argv[-1]
int(PORT)

# fmt:
# One of two things are recved: 1) vocab update, 2) history to stream chat response

async def handle_vocab(sock):
    global trie, vocab_raw

    # recv space-separated list of vocab
    vocab = await sock.recv()
    vocab = vocab.split(' ')

    print('updating vocab to', vocab)

    vocab_raw = vocab.copy()

    vocab += [v[0].upper() + v[1:] for v in vocab]
    vocab += [(' '+v if v.isalpha() else v) for v in vocab]

    vocab = list(set(vocab))

    # --- BUILD DA TRIE ---

    trie = {}

    for v in vocab:
        curr_node = trie

        toks = tokof(v, check=False)

        for tok in toks:
            if tok not in curr_node:
                curr_node[tok] = {}
            curr_node = curr_node[tok]

        curr_node[None] = {}
    
    # --- ok resp ---

    await sock.send('ok')

async def handle_stream(sock):
    n_msgs = int(await sock.recv())
    msgs = [await sock.recv() for i in range(n_msgs)]

    for tok in stream_response(msgs):
        await sock.send(tok)

async def handle_llm(sock):
    req_type = await sock.recv()

    if req_type == 'vocab':
        await handle_vocab(sock)
    if req_type == 'stream':
        await handle_stream(sock)

    # img = generate_img(prompt)
    # img_io = io.BytesIO()
    # img.save(img_io, format='png')
    # img_bytes = img_io.getvalue()
    
    # await sock.send(img_bytes)

async def main():
    server = await websockets.serve(handle_llm, "0.0.0.0", PORT, max_size=None)
    await server.wait_closed()

print('llm', f'{socket.gethostname()}:{PORT}', flush=True)
asyncio.run(main())
