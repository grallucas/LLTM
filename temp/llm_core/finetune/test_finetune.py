import torch
import torch.nn as nn
from transformers.models.qwen2.modeling_qwen2 import Qwen2DecoderLayer
from transformers import Qwen2ForCausalLM, Qwen2Config
import transformers
from matplotlib import pyplot as plt

class IMDecoderLayer(nn.Module):
    mask = None
    vspace_to_emb = None
    emb_to_vspace = None
    post_ff_norm = None
    block_strength = []

    def __init__(self, original_layer, emb_to_vspace, config, block_idx):
        super().__init__()
        self.original_layer = original_layer

        if IMDecoderLayer.vspace_to_emb == None:
            IMDecoderLayer.vspace_to_emb =  nn.Linear(config.vocab_size, config.hidden_size).to('cuda')
        
        if IMDecoderLayer.emb_to_vspace == None:
            IMDecoderLayer.emb_to_vspace =  emb_to_vspace

        if IMDecoderLayer.post_ff_norm == None:
            IMDecoderLayer.post_ff_norm = nn.RMSNorm(config.hidden_size).to('cuda')

        self.block_idx = len(IMDecoderLayer.block_strength)
        IMDecoderLayer.block_strength.append(
            nn.Parameter(torch.tensor(1.0, dtype=torch.float32).to('cuda'))
        )

    def forward(self, hidden_states, *args, **kwargs):
        hidden_states = self.original_layer(hidden_states, *args, **kwargs)
        hidden_states = hidden_states[0]

        residual = hidden_states
        hidden_states = IMDecoderLayer.emb_to_vspace(residual)
        
        assert IMDecoderLayer.mask
        max_vals, _ = hidden_states.max(axis=-1, keepdims=True)
        hidden_states -= max_vals
        hidden_states = -1*hidden_states.exp()
        
        for i, positions in enumerate(IMDecoderLayer.mask):
            for j, toks in enumerate(positions):
                if not len(toks):
                    hidden_states[i][j] *= 0
                    continue
                N = 1/len(toks)
                hidden_states[i][j][toks] = N

        hidden_states = IMDecoderLayer.vspace_to_emb(hidden_states)
        hidden_states = hidden_states * IMDecoderLayer.block_strength[self.block_idx]
        hidden_states = hidden_states + residual

        return (hidden_states,)


print('loading model')

MODEL_NAME = 'Qwen/Qwen2.5-0.5B-Instruct'

config = Qwen2Config.from_pretrained(MODEL_NAME)

model = Qwen2ForCausalLM.from_pretrained(MODEL_NAME).to('cuda')

# FREEZE existing model. Only the new layer in IMDecoderLayer will be trained
for param in model.parameters():
    param.requires_grad = False

tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_NAME)

for i, _ in enumerate(model.model.layers):
    model.model.layers[i] = IMDecoderLayer(model.model.layers[i], model.lm_head, config, i)

print(model)

import json
from tqdm.notebook import tqdm
import gc

EPOCHS = 1
BATCH_SIZE = 1

optimizer = torch.optim.AdamW(
    [p for p in IMDecoderLayer.vspace_to_emb.parameters() if p.requires_grad]+
    [p for p in IMDecoderLayer.post_ff_norm.parameters() if p.requires_grad]+
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
            mask = [] # mask[batch, position, allowed_tok]
            for batch_size in tokens['attention_mask'].argmin(axis=1):
                if batch_size == 0:
                    batch_size = tokens['attention_mask'].shape[1]
                mask.append([[] for i in range(batch_size)])
            for batch_id, batch_tokens in enumerate(tokens['input_ids']):
                for pos_id, tok in enumerate(batch_tokens):
                    if tok == 151643:
                        continue
                    mask[batch_id][pos_id].append(tok)
            IMDecoderLayer.mask = mask
            
            outputs = model(**tokens, labels=tokens['input_ids'])
            loss = outputs.loss

            loss.backward()
            optimizer.step()

            loss_avg = float(loss)/BATCH_SIZE
            losses.append(loss_avg)

            if i%10 == 0:
                print('did', i, flush=True)
                torch.save(IMDecoderLayer.vspace_to_emb.state_dict(), '/data/ai_club/team_3_2024-25/weights/vspace_to_emb4.pth')
                torch.save(IMDecoderLayer.post_ff_norm.state_dict(), '/data/ai_club/team_3_2024-25/weights/post_ff_norm4.pth')
                with open('/data/ai_club/team_3_2024-25/weights/block_strength4.json', 'w') as f:
                    json.dump([float(x) for x in IMDecoderLayer.block_strength], f)
        except torch.OutOfMemoryError:
            print(f'OOM on {i}', flush=True)
            try: del tokens, outputs
            except NameError: pass
            gc.collect()
        i += 1

torch.save(IMDecoderLayer.vspace_to_emb.state_dict(), '/data/ai_club/team_3_2024-25/weights/vspace_to_emb4.pth')
torch.save(IMDecoderLayer.post_ff_norm.state_dict(), '/data/ai_club/team_3_2024-25/weights/post_ff_norm4.pth')
with open('/data/ai_club/team_3_2024-25/weights/block_strength4.json', 'w') as f:
    json.dump([float(x) for x in IMDecoderLayer.block_strength], f)

with open('losses2.json','w') as f:
    json.dump(losses, f)