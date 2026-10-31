import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='/', 
intents=discord.Intents.all()
)

# Token For Bot
TOKEN = os.getenv("DISCORD_TOKEN")


# Bot Event
# command bot is ready

@bot.event
async def on_ready():
    print("Bot Online!")


# Server join-leave notifications

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1566213068671684709)
    text = f"welcome to the server, {member.mention}!"
    await channel.sent(text) # send message to channel


    @bot.event
    async def on_member_remove(member):
        channel = bot.get_channel(1566214048394117241)
        text = f"{member.mention} has left the server!"
        await channel.sent(text) # send message to channel

bot.run(TOKEN)
