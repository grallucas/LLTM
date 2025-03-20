import asyncio
import websockets

def generate_tts(prompt, host):
    async def generate():
        async with websockets.connect(f"ws://{host}") as sock:
            await sock.send(prompt)
            response = await sock.recv()
            
            return response

    return asyncio.run(generate())

def generate_img(prompt, host):
    async def generate():
        async with websockets.connect(f"ws://{host}") as sock:
            await sock.send(prompt)
            response = await sock.recv()
            
            return response
            
    return asyncio.run(generate())
