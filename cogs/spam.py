import disnake
from disnake.ext import commands
import random
import aiohttp
import asyncio
from utils import get_room_hash, spam_reactions, check_blacklist, CREATOR_ID, ROLE_ID, REGULAR_LIMIT, VIP_LIMIT
import string

class SpamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Spam reactions in a Quizizz room")
    @commands.cooldown(1, 30, type=commands.BucketType.user)
    async def spamreactions(self, ctx, room_code: str, duration: int):
        await ctx.response.defer(ephemeral=True)
        
        if ctx.author.id != CREATOR_ID and ROLE_ID not in [role.id for role in ctx.author.roles]:
            await self.send_error(ctx, "You do not have the required role to use this command.")
            return

        limit = 120 if any(role.id == ROLE_ID for role in ctx.author.roles) else 60
        if ctx.author.id != CREATOR_ID and duration > limit:
            await self.send_error(ctx, f"You can spam reactions for up to {limit} seconds.")
            return

        try:
            room_hash = await get_room_hash(room_code)
            embed = disnake.Embed(
                title="Spam Reactions",
                description=f"Starting spam for {duration} seconds in room {room_code}!",
                color=disnake.Color.blue())
            embed.set_footer(text="by dsc.gg/quizizbots")
            await ctx.edit_original_response(embed=embed)
            await spam_reactions(duration, room_hash)
        except ValueError as e:
            await self.send_error(ctx, str(e))

    async def send_error(self, ctx, message):
        embed = disnake.Embed(
            title="Error",
            description=message,
            color=disnake.Color.red())
        embed.set_footer(text="by dsc.gg/quizizbots")
        await ctx.edit_original_response(embed=embed)

    @commands.slash_command(description="Add player/players to room")
    @commands.cooldown(1, 10, type=commands.BucketType.user)
    async def addplayer(self, ctx, roomcode: str, playername: str = "", amount: int = 1):
        await ctx.response.defer(ephemeral=True)

        if ctx.author.id != CREATOR_ID and amount > REGULAR_LIMIT:
            await self.send_error(ctx, f"You can add up to {REGULAR_LIMIT} players at a time.")
            return

        if ctx.author.id == CREATOR_ID:
            limit = amount
        else:
            limit = VIP_LIMIT if any(role.id == ROLE_ID for role in ctx.author.roles) else REGULAR_LIMIT
            if amount > limit:
                await self.send_error(ctx, f"You can add up to {limit} players at a time.")
                return

        success = 0
        async with aiohttp.ClientSession() as session:
            async with session.post('https://game.quizizz.com/play-api/v5/checkRoom', json={"roomCode": roomcode}) as resp:
                if resp.status != 200:
                    await self.send_error(ctx, "Invalid Room Code!")
                    return
                rdata = await resp.json()
                roomhash = rdata.get('room', {}).get('hash')
                if not roomhash:
                    await self.send_error(ctx, "Invalid Room Code!")
                    return

                tasks = []
                for i in range(amount):
                    playername_final = playername or ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                    fakeip = f"{random.randint(100, 255)}.{random.randint(100, 255)}.{random.randint(100, 255)}.{random.randint(100, 255)}"
                    task = asyncio.create_task(self.add_bot(session, roomhash, playername_final, fakeip, i))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                success = sum(results)

        await ctx.send(f"Successfully Added {success} Bots to `{roomcode}`", ephemeral=True)

    async def add_bot(self, session, roomhash, playername, fakeip, index):
        async with session.post("https://game.quizizz.com/play-api/v5/join",
                                json={
                                    "roomHash": roomhash,
                                    "player": {
                                        "id": playername + str(index),
                                        "origin": "web",
                                        "isGoogleAuth": False,
                                        "avatarId": random.randint(1, 10)
                                    },
                                    "__cid__": "v5/join.|1.1632599434062",
                                    "ip": fakeip
                                }) as resp:
            return resp.status == 200

    @commands.slash_command(description="Add Powerup to player")
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def addpowerup(self, ctx, roomcode: str, name: str, powerup: str):
        if await check_blacklist(str(ctx.author.id)):
            embed = disnake.Embed(
                title="Error",
                description="You're currently in the blacklist, you can't use any command except someone clears the blacklist.",
                color=disnake.Color.red())
            embed.set_footer(text="by dsc.gg/quizizbots")
            await ctx.send(embed=embed, ephemeral=True)
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
            "All": [{
                "name": "2x",
                "meta": {
                    "beltPosition": 0
                }
            }, {
                "name": "double-jeopardy",
                "meta": {
                    "beltPosition": 1
                }
            }, {
                "name": "50-50",
                "meta": {
                    "beltPosition": 2
                }
            }, {
                "name": "immunity",
                "meta": {
                    "beltPosition": 3
                }
            }, {
                "name": "time-freeze",
                "meta": {
                    "beltPosition": 4
                }
            }, {
                "name": "power-play",
                "meta": {
                    "beltPosition": 5
                }
            }, {
                "name": "streak-saver",
                "meta": {
                    "beltPosition": 6
                }
            }, {
                "name": "glitch",
                "meta": {
                    "beltPosition": 7
                }
            }, {
                "name": "streak-booster",
                "meta": {
                    "beltPosition": 8
                }
            }, {
                "name": "supersonic",
                "meta": {
                    "beltPosition": 9
                }
            }, {
                "name": "eraser",
                "meta": {
                    "beltPosition": 10
                }
            }]
        }

        raw_powerup = powerup_mapping.get(powerup)
        if not raw_powerup:
            embed = disnake.Embed(title="Error",
                              description="Invalid powerup selected!",
                              color=disnake.Color.red()
                              )
            embed.set_footer(text="by dsc.gg/quizizbots")
            await ctx.send(embed=embed, ephemeral=True)
            return

        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://game.quizizz.com/play-api/v5/checkRoom',
                json={"roomCode": roomcode}) as response:
                rdata = (await response.json()).get('room')
                if not rdata:
                    embed = disnake.Embed(
                        title="Error",
                        description="Invalid Quizizz Room Code! Make sure you type correct room code.",
                        color=disnake.Color.red())
                    embed.set_footer(text="by dsc.gg/quizizbots")
                    await ctx.send(embed=embed, ephemeral=True)
                    return

                if rdata.get('powerups') == 'no':
                    embed = disnake.Embed(
                        title="Error",
                        description="This quizizz room has disabled powerup!",
                        color=disnake.Color.red())
                    embed.set_footer(text="by dsc.gg/quizizbots")
                    await ctx.send(embed=embed, ephemeral=True)
                    return

                roomhash = rdata.get('hash')
                gtype = rdata.get('type')

                if powerup == "All":
                    addpowerup = await session.post(
                        'https://game.quizizz.com/play-api/awardPowerups',
                        json={
                            "roomHash": roomhash,
                            "playerId": name,
                            "powerups": raw_powerup,
                            "gameType": gtype
                        })
                else:
                    addpowerup = await session.post(
                        'https://game.quizizz.com/play-api/awardPowerup',
                        json={
                            "roomHash": roomhash,
                            "playerId": name,
                            "powerup": {
                                "name": raw_powerup
                            },
                            "gameType": gtype
                        })

                if addpowerup.status == 200:
                    embed = disnake.Embed(
                    title="Success",
                    description=f"Successfully Added that Powerup to `{name}`. If you don't see the powerup, reload the page.",
                    color=disnake.Color.green())
                    embed.set_footer(text="by dsc.gg/quizizbots")
                    await ctx.send(embed=embed, ephemeral=True)
                else:
                    embed = disnake.Embed(
                    title="Error",
                    description="Failed to add that powerup, are you sure you entered the correct name?",
                    color=disnake.Color.red())
                    embed.set_footer(text="by dsc.gg/quizizbots")
                    await ctx.send(embed=embed, ephemeral=True)

    @commands.slash_command(description="Add Powerup to all players in a room (Creator only)")
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def addpowerupall(self, ctx, roomcode: str, powerup: str):
        if ctx.author.id != CREATOR_ID:
            await self.send_error(ctx, "You do not have permission to use this command.")
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
            "All": [{
                "name": "2x",
                "meta": {
                    "beltPosition": 0
                }
            }, {
                "name": "double-jeopardy",
                "meta": {
                    "beltPosition": 1
                }
            }, {
                "name": "50-50",
                "meta": {
                    "beltPosition": 2
                }
            }, {
                "name": "immunity",
                "meta": {
                    "beltPosition": 3
                }
            }, {
                "name": "time-freeze",
                "meta": {
                    "beltPosition": 4
                }
            }, {
                "name": "power-play",
                "meta": {
                    "beltPosition": 5
                }
            }, {
                "name": "streak-saver",
                "meta": {
                    "beltPosition": 6
                }
            }, {
                "name": "glitch",
                "meta": {
                    "beltPosition": 7
                }
            }, {
                "name": "streak-booster",
                "meta": {
                    "beltPosition": 8
                }
            }, {
                "name": "supersonic",
                "meta": {
                    "beltPosition": 9
                }
            }, {
                "name": "eraser",
                "meta": {
                    "beltPosition": 10
                }
            }]
        }

        raw_powerup = powerup_mapping.get(powerup)
        if not raw_powerup:
            embed = disnake.Embed(title="Error",
                              description="Invalid powerup selected!",
                              color=disnake.Color.red()
                              )
            embed.set_footer(text="by dsc.gg/quizizbots")
            await ctx.send(embed=embed, ephemeral=True)
            return

        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://game.quizizz.com/play-api/v5/checkRoom',
                json={"roomCode": roomcode}) as response:
                rdata = (await response.json()).get('room')
                if not rdata:
                    embed = disnake.Embed(
                        title="Error",
                        description="Invalid Quizizz Room Code! Make sure you type correct room code.",
                        color=disnake.Color.red())
                    embed.set_footer(text="by dsc.gg/quizizbots")
                    await ctx.send(embed=embed, ephemeral=True)
                    return

                if rdata.get('powerups') == 'no':
                    embed = disnake.Embed(
                        title="Error",
                        description="This quizizz room has disabled powerup!",
                        color=disnake.Color.red())
                    embed.set_footer(text="by dsc.gg/quizizbots")
                    await ctx.send(embed=embed, ephemeral=True)
                    return

                roomhash = rdata.get('hash')
                gtype = rdata.get('type')
                players = rdata.get('players', [])

                tasks = []
                for player in players:
                    player_id = player.get('id')
                    if powerup == "All":
                        task = asyncio.create_task(session.post(
                            'https://game.quizizz.com/play-api/awardPowerups',
                            json={
                                "roomHash": roomhash,
                                "playerId": player_id,
                                "powerups": raw_powerup,
                                "gameType": gtype
                            }))
                    else:
                        task = asyncio.create_task(session.post(
                            'https://game.quizizz.com/play-api/awardPowerup',
                            json={
                                "roomHash": roomhash,
                                "playerId": player_id,
                                "powerup": {
                                    "name": raw_powerup
                                },
                                "gameType": gtype
                            }))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)

                success_count = sum(result.status == 200 for result in results)
                fail_count = len(players) - success_count

                if success_count > 0:
                    embed = disnake.Embed(
                        title="Success",
                        description=f"Successfully added {powerup} to {success_count} players.",
                        color=disnake.Color.green())
                if fail_count > 0:
                    embed = disnake.Embed(
                        title="Error",
                        description=f"Failed to add {powerup} to {fail_count} players.",
                        color=disnake.Color.red())
                embed.set_footer(text="by dsc.gg/quizizbots")
                await ctx.send(embed=embed, ephemeral=True)