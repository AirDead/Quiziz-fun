import disnake
from disnake.ext import commands
from datetime import datetime
import requests
import io

def create_help_page(page_num=0):
    help_data = {
        "Cheat Commands": {
            "</addplayer:950656396444172338>": "Add player/players to room.",
            "</addpowerup:928500685102776352>": "Add powerup to player.",
            "</getroominfo:958753737600536616>": "Export room info.",
            "</roomfinder:928500685102776353>": "Find an active Quizizz room.",
            "</spamreactions:1078358844771668058>": "Spam reaction."
        },
        "Other Commands": {
            "</help:963096500848697384>": "Show help.",
            "</ping:981358400568975440>": "Ping!"
        }
    }

    page_num = page_num % len(list(help_data))
    title = list(help_data)[page_num]
    embed = disnake.Embed(title=title)

    for command, description in help_data[title].items():
        embed.add_field(name=command, value=description, inline=False)

    embed.set_footer(text=f"Page {page_num + 1} of {len(list(help_data))}")
    return embed

class HelpObject(disnake.ui.View):

    def __init__(self, author: disnake.User, alt_res: disnake.ApplicationCommandInteraction):
        super().__init__(timeout=120)
        self.current_page = 0
        self.author = author
        self.alt_res = alt_res

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        embed = create_help_page(self.current_page)
        embed.set_footer(text="Timeout exceeded!")
        await self.alt_res.edit_original_message(embed=embed, view=self)

    @disnake.ui.button(label="<", style=disnake.ButtonStyle.green)
    async def prev_callback(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.current_page -= 1
        await interaction.response.edit_message(embed=create_help_page(self.current_page))

    @disnake.ui.button(label=">", style=disnake.ButtonStyle.green)
    async def next_callback(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.current_page += 1
        await interaction.response.edit_message(embed=create_help_page(self.current_page))

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Pong!")
    async def ping(self, ctx):
        embed = disnake.Embed(title=" ", color=disnake.Color.random())
        embed.set_author(name="Pong!")
        embed.add_field(name="Latency", value="`{} ms`".format(self.bot.latency * 1000), inline=True)
        embed.set_footer(text=str(datetime.now()))
        await ctx.send(embed=embed)

    @commands.slash_command(description="Show list of commands")
    async def help(self, ctx: disnake.ApplicationCommandInteraction):
        await ctx.response.defer()
        await ctx.send(embed=create_help_page(), view=HelpObject(author=ctx.author, alt_res=ctx))

    @commands.slash_command(description="Export room info")
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def getroominfo(self, ctx, roomcode: str):
        room = requests.post('https://game.quizizz.com/play-api/v5/checkRoom', json={"roomCode": roomcode})
        if not room.json().get("room"):
            await ctx.send("Invalid Room Code!", ephemeral=True)
        else:
            await ctx.send(file=disnake.File(io.StringIO(str(room.json())), "info.json"))
