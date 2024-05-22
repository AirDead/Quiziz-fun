import disnake
from disnake.ext import commands
import aiohttp
from utils import check_blacklist, CREATOR_ID, ROLE_ID

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Add Powerup to all players")
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def addpoweruptoall(self, ctx, roomcode: str, powerup: str):
        await ctx.response.defer(ephemeral=True)
        
        if await check_blacklist(str(ctx.author.id)):
            await self.send_error(ctx, "You're currently in the blacklist, you can't use any command except someone clears the blacklist.")
            return

        if ctx.author.id != CREATOR_ID and ROLE_ID not in [role.id for role in ctx.author.roles]:
            await self.send_error(ctx, "You do not have the required role to use this command.")
            return

        powerup_mapping = {
            "Double Jeopardy": "double-jeopardy",
            "X2": "2x",
            "50-50": "50-50",
            "Eraser": "eraser",
            "Immunity": "immunity",
            "Time Freeze": "time-freeze",
            "Power Play": "power-play",
            "Streak Saver": "streak-saver",
            "Glitch": "glitch",
            "Streak Booster": "streak-booster",
            "Super Sonic": "supersonic",
            "All": [
                {"name": "2x", "meta": {"beltPosition": 0}},
                {"name": "double-jeopardy", "meta": {"beltPosition": 1}},
                {"name": "50-50", "meta": {"beltPosition": 2}},
                {"name": "immunity", "meta": {"beltPosition": 3}},
                {"name": "time-freeze", "meta": {"beltPosition": 4}},
                {"name": "power-play", "meta": {"beltPosition": 5}},
                {"name": "streak-saver", "meta": {"beltPosition": 6}},
                {"name": "glitch", "meta": {"beltPosition": 7}},
                {"name": "streak-booster", "meta": {"beltPosition": 8}},
                {"name": "supersonic", "meta": {"beltPosition": 9}},
                {"name": "eraser", "meta": {"beltPosition": 10}}
            ]
        }

        raw_powerup = powerup_mapping.get(powerup)
        if not raw_powerup:
            await self.send_error(ctx, "Invalid powerup selected!")
            return

        async with aiohttp.ClientSession() as session:
            async with session.post('https://game.quizizz.com/play-api/v5/checkRoom', json={"roomCode": roomcode}) as response:
                if response.status != 200:
                    await self.send_error(ctx, "Invalid Quizizz Room Code! Make sure you type the correct room code.")
                    return
                
                rdata = (await response.json()).get('room')
                if not rdata:
                    await self.send_error(ctx, "Invalid Quizizz Room Code! Make sure you type the correct room code.")
                    return

                if rdata.get('powerups') == 'no':
                    await self.send_error(ctx, "This Quizizz room has disabled powerups!")
                    return

                roomhash = rdata.get('hash')
                gtype = rdata.get('type')

                async with session.get(f'https://game.quizizz.com/play-api/v5/rooms/{roomhash}/players') as player_response:
                    players = await player_response.json()
                    player_ids = [player['id'] for player in players.get('data', [])]

                if not player_ids:
                    await self.send_error(ctx, "No players found in the room.")
                    return

                tasks = []
                if powerup == "All":
                    tasks.append(self.award_powerups(session, roomhash, player_ids, raw_powerup, gtype))
                else:
                    for player_id in player_ids:
                        tasks.append(self.award_powerup(session, roomhash, player_id, raw_powerup, gtype))

                results = await asyncio.gather(*tasks)
                if all(results):
                    await self.send_success(ctx, "Successfully added the powerup to all players. If you don't see the powerup, reload the page.")
                else:
                    await self.send_error(ctx, "Failed to add the powerup to all players.")

    async def award_powerups(self, session, roomhash, player_ids, powerups, gtype):
        async with session.post(
                'https://game.quizizz.com/play-api/awardPowerups',
                json={
                    "roomHash": roomhash,
                    "playerIds": player_ids,
                    "powerups": powerups,
                    "gameType": gtype
                }) as response:
            return response.status == 200

    async def award_powerup(self, session, roomhash, player_id, powerup, gtype):
        async with session.post(
                'https://game.quizizz.com/play-api/awardPowerup',
                json={
                    "roomHash": roomhash,
                    "playerId": player_id,
                    "powerup": {
                        "name": powerup
                    },
                    "gameType": gtype
                }) as response:
            return response.status == 200

    async def send_error(self, ctx, message):
        embed = disnake.Embed(
            title="Error",
            description=message,
            color=disnake.Color.red())
        embed.set_footer(text="by dsc.gg/quizizbots")
        await ctx.edit_original_response(embed=embed)

    async def send_success(self, ctx, message):
        embed = disnake.Embed(
            title="Success",
            description=message,
            color=disnake.Color.green())
        embed.set_footer(text="by dsc.gg/quizizbots")
        await ctx.edit_original_response(embed=embed)