import disnake
from disnake.ext import commands
import asyncio
from cogs import admin, utility, spam
from rich_presence import setup_rich_presence

bot = commands.InteractionBot()

# Register cogs
bot.add_cog(admin.AdminCog(bot))
bot.add_cog(utility.UtilityCog(bot))
bot.add_cog(spam.SpamCog(bot))

@bot.event
async def on_ready():
    await setup_rich_presence(bot)
    print("The bot is ready!")

# Run the bot with the token
bot.run("MTI0Mjc1MjE5MzIyOTIyNjA2NQ.Giqa-F.0wvn3PizvkUUoz8qpkMKjxjiIQ-AbiJE9QLqGI")
