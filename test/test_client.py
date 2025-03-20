'''
bash -c "source /data/ai_club/team_3_2024-25/team3-env-py312-glibc/bin/activate; python ./test_client.py"
'''

import asyncio
import websockets

async def receive_text():
    async with websockets.connect("ws://dh-node7:8001") as sock:
        await sock.send("Hei")
        response = await sock.recv()
        
        print(response[:100])

asyncio.run(receive_text())
