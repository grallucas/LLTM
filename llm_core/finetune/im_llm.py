import os

MODE = None
if os.environ['IM_MODE'] == 'old-mask_new-ops':
    MODE = 'omno'
if os.environ['IM_MODE'] == 'new-mask_old-ops':
    MODE = 'nmoo'
if os.environ['IM_MODE'] == 'new-mask_ops2':
    MODE = 'nmo2'
if not MODE:
    raise Exception(f'Need to specify cli mode. Got {MODE} for {os.environ["IM_MODE"]}')

import torch
import torch.nn as nn
from transformers.models.qwen2.modeling_qwen2 import Qwen2DecoderLayer
from transformers import Qwen2ForCausalLM, Qwen2Config
import transformers
import json
import gc

class IMDecoderLayer(nn.Module):
    mask = None
    vspace_to_emb = None
    emb_to_vspace = None
    # post_ff_norm = None
    block_strength = []

    scratch = None
    norm = None

    def __init__(self, original_layer, emb_to_vspace, vspace_to_emb, norm, config, block_idx):
        super().__init__()
        self.original_layer = original_layer

        if IMDecoderLayer.vspace_to_emb == None:
            if MODE == 'omno' or MODE == 'nmoo':
                IMDecoderLayer.vspace_to_emb =  nn.Linear(config.vocab_size, config.hidden_size).to('cuda')
            if MODE == 'nmo2':
                IMDecoderLayer.vspace_to_emb = vspace_to_emb

        if IMDecoderLayer.emb_to_vspace == None:
            IMDecoderLayer.emb_to_vspace =  emb_to_vspace

        if IMDecoderLayer.scratch == None:
            IMDecoderLayer.scratch = torch.zeros(config.vocab_size, dtype=bool).to('cuda')

        # if IMDecoderLayer.post_ff_norm == None:
        #     IMDecoderLayer.post_ff_norm = nn.RMSNorm(config.hidden_size).to('cuda')

        if IMDecoderLayer.norm == None:
            IMDecoderLayer.norm = norm

        self.block_idx = len(IMDecoderLayer.block_strength)
        IMDecoderLayer.block_strength.append(
            nn.Parameter(torch.tensor(1.0, dtype=torch.float32).to('cuda'))
        )

        # if MODE == 'nmoo':
            # TODO: detatch index
            # self.temp_mask = torch.zeros(config.vocab_size).to('cuda')

    def forward(self, hidden_states, *args, **kwargs):
        hidden_states = self.original_layer(hidden_states, *args, **kwargs)
        hidden_states = hidden_states[0]

        residual = hidden_states
        hidden_states = IMDecoderLayer.emb_to_vspace(residual)
        
        assert IMDecoderLayer.mask != None

        if MODE == 'omno':
            max_vals, _ = hidden_states.max(axis=-1, keepdims=True)
            hidden_states -= max_vals
            hidden_states = -1*hidden_states.exp()
            
            if len(IMDecoderLayer.mask) == 0:
                hidden_states *= 0
            else:
                hidden_states[:,:,IMDecoderLayer.mask] = 1/len(IMDecoderLayer.mask)
        if MODE == 'nmoo':
            for i, positions in enumerate(IMDecoderLayer.mask):
                for j, toks in enumerate(positions):
                    # TODO: detatch mask

                    # self.temp_mask *= 0
                    # # if len(toks) == 0:
                    # #     self.mask += 1
                    # # else:
                    # self.temp_mask[toks] += 1 
                    # hidden_states[i][j] *= self.temp_mask

                    # toks_inv = torch.ones(len(hidden_states[i][j]), dtype=bool).to('cuda')
                    # toks_inv[toks] = False
                    # hidden_states[i][j][toks_inv] *= 0

                    # for k in range(len(hidden_states[i][j])):
                    #     if k not in toks:
                    #         hidden_states[i,j,k] = 0

                    # temp = hidden_states[i,j,:].clone()
                    # temp[toks] = 0
                    # hidden_states[i,j,:] -= temp

                    # a way to try zeroing all that I dont have indices for
                    hidden_states[i,j,toks] *= 1e4
                    hidden_states[i,j,:] /= 1e4
        if MODE == 'nmo2':
            for i, positions in enumerate(IMDecoderLayer.mask):
                for j, toks_allowed in enumerate(positions):
                    if not toks_allowed:
                        hidden_states[i,j,:] = 0 
                        continue

                    hidden_states[i,j,:] = 0 

                    IMDecoderLayer.scratch[:] = False
                    IMDecoderLayer.scratch[toks_allowed] = True
                    hidden_states[i,j,IMDecoderLayer.scratch] += 1/IMDecoderLayer.scratch.sum()

                    IMDecoderLayer.scratch[:] = True
                    IMDecoderLayer.scratch[toks_allowed] = False
                    hidden_states[i,j,IMDecoderLayer.scratch] -= 1/IMDecoderLayer.scratch.sum()

        # max_vals, _ = hidden_states.max(axis=-1, keepdims=True)
        # hidden_states -= max_vals
        # hidden_states = -1*hidden_states.exp()
        
        # for i, positions in enumerate(IMDecoderLayer.mask):
        #     for j, toks in enumerate(positions):
        #         if not len(toks):
        #             hidden_states[i][j] *= 0
        #             continue
        #         N = 1/len(toks)
        #         hidden_states[i][j][toks] = N

        # hidden_states = IMDecoderLayer.vspace_to_emb(hidden_states)

        # print(hidden_states)
        hidden_states = hidden_states @ IMDecoderLayer.vspace_to_emb.weight
        hidden_states = hidden_states * IMDecoderLayer.block_strength[self.block_idx]
        hidden_states = hidden_states + residual

        return (hidden_states,)

def get_model():
    MODEL_NAME = 'Qwen/Qwen2.5-0.5B-Instruct'

    config = Qwen2Config.from_pretrained(MODEL_NAME)

    model = Qwen2ForCausalLM.from_pretrained(MODEL_NAME).to('cuda')

    # FREEZE existing model. Only the new layer in IMDecoderLayer will be trained
    for param in model.parameters():
        param.requires_grad = False

    tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_NAME)

    # REPLACE transformer blocks with IM ones
    for i, _ in enumerate(model.model.layers):
        model.model.layers[i] = IMDecoderLayer(model.model.layers[i], model.lm_head, model.model.embed_tokens, model.model.norm, config, i)

    def tokenize(batch):
        tokens = tokenizer(batch, return_tensors='pt', padding=True)
        tokens = {k:v.to('cuda') for k,v in tokens.items()}
        return tokens

    def tokof(s):
        toks = tokenizer(s)['input_ids']
        assert len(toks) == 1 # TOK OF only for single tok strs
        return toks[0]

    return model, tokenize, tokenizer, tokof

def save_weights(id):
    # torch.save(IMDecoderLayer.vspace_to_emb.state_dict(), f'/data/ai_club/team_3_2024-25/weights/vspace_to_emb{id}.pth')
    # torch.save(IMDecoderLayer.post_ff_norm.state_dict(), f'/data/ai_club/team_3_2024-25/weights/post_ff_norm{id}.pth')

    with open(f'/data/ai_club/team_3_2024-25/weights/block_strength{id}.json', 'w') as f:
        json.dump([float(x) for x in IMDecoderLayer.block_strength], f)

def load_weights(id):
    # IMDecoderLayer.vspace_to_emb.load_state_dict(torch.load(f'/data/ai_club/team_3_2024-25/weights/vspace_to_emb{id}.pth'))
    # IMDecoderLayer.post_ff_norm.load_state_dict(torch.load(f'/data/ai_club/team_3_2024-25/weights/post_ff_norm{id}.pth'))

    with open(f'/data/ai_club/team_3_2024-25/weights/block_strength{id}.json', 'r') as f:
        block_strength_weights = json.load(f)
    for i, _ in enumerate(IMDecoderLayer.block_strength):
        IMDecoderLayer.block_strength[i] = nn.Parameter(torch.tensor(block_strength_weights[i], dtype=torch.float32).to('cuda'))

def gen_mask(tokens):
    mask = [] # mask[batch, position, allowed_tok]
    for batch_size in tokens['attention_mask'].argmin(axis=1):
        if batch_size == 0:
            batch_size = tokens['attention_mask'].shape[1]
        mask.append([[] for i in range(batch_size)])

    return mask

def train(model, tokenizer, save_id):
    EPOCHS = 1
    BATCH_SIZE = 1

    optimizer = torch.optim.AdamW(
        [p for p in IMDecoderLayer.vspace_to_emb.parameters() if p.requires_grad]+
        # [p for p in IMDecoderLayer.post_ff_norm.parameters() if p.requires_grad]+
        IMDecoderLayer.block_strength,
        lr=5e-5
    )

    with open('/data/ai_club/team_3_2024-25/datasets/alpaca_data_cleaned.json', 'r') as f:
        data = [x['output'] for x in json.load(f)]

    # LIMIT for now
    data = data[:10_000]

    dataloader = torch.utils.data.DataLoader(data, batch_size=BATCH_SIZE, shuffle=True)

    losses = []

    print('training')

    for epoch in range(EPOCHS):
        i = 0
        for batch in dataloader:
            try:
                optimizer.zero_grad()

                tokens = tokenizer(batch, return_tensors='pt', padding=True)
                tokens = {k:v.to('cuda') for k,v in tokens.items()}

                # set mask from batch
                if MODE == 'omno':
                    IMDecoderLayer.mask = tokens['input_ids'].unique()
                if MODE == 'nmoo':
                    mask = gen_mask(tokens)
                    # fill mask with same tokes as batch
                    for seq_i, tok_seq in enumerate(tokens['input_ids']):
                        for tok_i, tok in enumerate(tok_seq):
                            mask_part = mask[seq_i]
                            if tok_i >= len(mask_part):
                                continue
                            mask_part[tok_i].append(int(tok))
                    IMDecoderLayer.mask = mask

                # mask = gen_mask(tokens)
                # for batch_id, batch_tokens in enumerate(tokens['input_ids']):
                #     for pos_id, tok in enumerate(batch_tokens):
                #         if tok == 151643:
                #             continue
                #         mask[batch_id][pos_id].append(tok)
                # IMDecoderLayer.mask = mask
                
                outputs = model(**tokens, labels=tokens['input_ids'])
                loss = outputs.loss

                loss.backward()
                optimizer.step()

                loss_avg = float(loss)/BATCH_SIZE
                losses.append(loss_avg)

                if i%10 == 0:
                    save_weights(save_id)
                    print(f'Did {i}', flush=True)
            except torch.OutOfMemoryError:
                print(f'OOM on {i}', flush=True)
                try: del tokens, outputs
                except NameError: pass
                gc.collect()
            i += 1

    save_weights(save_id)

    with open(f'/data/ai_club/team_3_2024-25/weights/losses{save_id}.json','w') as f:
        json.dump(losses, f)

if __name__ == '__main__':
    import sys

    torch.autograd.set_detect_anomaly(True)

    print('STARTING', flush=True)

    model, tokenize, tokenizer, tokof = get_model()
    print(model)

    train(model, tokenizer, int(sys.argv[-1]))