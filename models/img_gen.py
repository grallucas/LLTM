from diffusers import AutoPipelineForText2Image
import torch

pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16")
pipe.to("cuda:0")

def generate_img(prompt):
    image = pipe(prompt=prompt, num_inference_steps=1, guidance_scale=0.0).images[0]
    return image

# --- server :( ---

import asyncio
import websockets
import socket
import sys
import io

PORT = sys.argv[-1]
int(PORT)

async def handle_tts(sock):
    prompt = await sock.recv()

    img = generate_img(prompt)
    img_io = io.BytesIO()
    img.save(img_io, format='png')
    img_bytes = img_io.getvalue()
    
    await sock.send(img_bytes)

async def main():
    server = await websockets.serve(handle_tts, "0.0.0.0", PORT, max_size=None)
    await server.wait_closed()

print('img_gen', f'{socket.gethostname()}:{PORT}', flush=True)
asyncio.run(main())
