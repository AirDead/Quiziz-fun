import disnake

async def setup_rich_presence(bot):
    activity = disnake.Activity(
        type=disnake.ActivityType.watching,
        name="Fucking quizizz | /help"
    )
    await bot.change_presence(activity=activity)
