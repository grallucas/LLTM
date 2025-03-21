from transformers import VitsModel, AutoTokenizer
import torch
import numpy as np

model = VitsModel.from_pretrained("facebook/mms-tts-fin")
tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-fin")

model.to('cuda:0')

def create_wav_header(num_channels, sample_rate, num_samples, bits_per_sample):
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    subchunk2_size = num_samples * num_channels * bits_per_sample // 8
    chunk_size = 36 + subchunk2_size

    header = b'RIFF'
    header += (chunk_size).to_bytes(4, byteorder='little')
    header += b'WAVE'
    header += b'fmt '
    header += (16).to_bytes(4, byteorder='little')  # Subchunk1Size (16 for PCM)
    header += (1).to_bytes(2, byteorder='little')  # AudioFormat (1 for PCM)
    header += (num_channels).to_bytes(2, byteorder='little')
    header += (sample_rate).to_bytes(4, byteorder='little')
    header += (byte_rate).to_bytes(4, byteorder='little')
    header += (block_align).to_bytes(2, byteorder='little')
    header += (bits_per_sample).to_bytes(2, byteorder='little')
    header += b'data'
    header += (subchunk2_size).to_bytes(4, byteorder='little')
    
    return header

def generate_audio(text):
    text = text.replace('c', 'k').replace('w', 'v') # FIX FOR FINNISH. TODO: generalize to any lang

    inputs = tokenizer(text, return_tensors="pt")
    inputs = {k:v.to('cuda:0') for k,v in inputs.items()}

    with torch.no_grad():
        output = (model(**inputs).waveform[0]*32767.0).to('cpu').numpy().astype(np.int16)

    # FREE gpu memory
    for k in list(inputs.keys()): del inputs[k]
    torch.cuda.empty_cache()

    return create_wav_header(1, model.config.sampling_rate, output.shape[-1], 16) + output.tobytes()

# --- server :( ---

import asyncio
import websockets
import socket
import sys

PORT = sys.argv[-1]
int(PORT)

async def handle_tts(sock):
    prompt = await sock.recv()
    audio = generate_audio(prompt)

    await sock.send(audio)

async def main():
    server = await websockets.serve(handle_tts, "0.0.0.0", PORT, max_size=None)
    await server.wait_closed()

print('tts', f'{socket.gethostname()}:{PORT}', flush=True)
asyncio.run(main())
