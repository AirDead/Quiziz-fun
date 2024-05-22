import aiohttp
import random
import time 
import asyncio

BLACKLIST_FILE = "blacklist.txt"
ROLE_ID = 1242936108753354892
VIP_LIMIT = 500
REGULAR_LIMIT = 50
CREATOR_ID = 1195096721433317416

async def check_blacklist(user_id):
    try:
        with open(BLACKLIST_FILE, "r") as file:
            blacklist = file.read().split()
        return user_id in blacklist
    except FileNotFoundError:
        return False

async def spam_reactions(duration: int, hashCode: str):
    url = "https://game.quizizz.com/play-api/reactionUpdate"
    json_data = {
        "playerId": "spam by dsc.gg/schoolhacks",
        "roomHash": hashCode,
        "triggerType": "live-reaction",
        "reactionDetail": {"id": 4, "intensity": 1}
    }

    async with aiohttp.ClientSession() as session:
        end_time = time.time() + duration
        while time.time() < end_time:
            async with session.post(url, json=json_data) as response:
                response_text = await response.text()
            await asyncio.sleep(0)  

async def get_room_hash(room_code: str) -> str:
    url = 'https://game.quizizz.com/play-api/v5/checkRoom'
    json_data = {"roomCode": room_code}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json_data) as response:
            room_data = await response.json()
            rdata = room_data.get('room')
            if not rdata:
                raise ValueError("Invalid Quizizz Room Code! Make sure you type correct room code.")
            return rdata.get('hash')
