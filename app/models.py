import asyncio
import websockets

def generate_tts(prompt, host):
    async def generate():
        async with websockets.connect(f"ws://{host}", max_size=None) as sock:
            await sock.send(prompt)
            response = await sock.recv()
            
            return response

    return asyncio.run(generate())

def generate_img(prompt, host):
    async def generate():
        async with websockets.connect(f"ws://{host}", max_size=None) as sock:
            await sock.send(prompt)
            response = await sock.recv()
            
            return response
            
    return asyncio.run(generate())

def llm_set_vocab(vocab, host):
    vocab = ' '.join(vocab)
    async def generate():
        async with websockets.connect(f"ws://{host}", max_size=None) as sock:
            await sock.send('vocab')
            await sock.send(vocab)
            resp = await sock.recv()

            return resp

    return asyncio.run(generate())

import threading
import queue

def llm_stream_chat(messages, host):
    output_queue = queue.Queue()

    async def generate():
        nonlocal messages
        async with websockets.connect(f"ws://{host}", max_size=None) as sock:
            await sock.send('stream')
            
            await sock.send(str(len(messages)))
            
            for msg in messages:
                await sock.send(msg)

            tok = None
            while tok != '<END>':
                tok = await sock.recv()
                output_queue.put(tok)

    def run_async_loop():
        asyncio.run(generate())

    thread = threading.Thread(target=run_async_loop, daemon=True)
    thread.start()

    while True:
        tok = output_queue.get()
        if tok == '<END>':
            break
        yield tok
