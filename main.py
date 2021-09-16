import discord
import ctypes
import sys
import os
import ctypes.util
from discord.ext import commands
from discord.errors import ClientException
from discord_components import Button, ButtonStyle
import MusicBot


opus = ctypes.util.find_library('opus')
discord.opus.load_opus(opus)
discord.opus.is_loaded()

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")


cogs = [MusicBot]
intents = discord.Intents.all()
intents.members = True
client = commands.Bot(command_prefix="-", intents=discord.Intents.all())

for cog in cogs:
    cog.setup(client)


@client.event
async def on_ready():
    print("Bot ready.")

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
