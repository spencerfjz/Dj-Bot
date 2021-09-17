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


@client.command(aliases=["prune", "clean"])
async def purge(ctx):
    deleted = await ctx.channel.purge(limit=100, check=lambda m: m.author == client.user)
    await ctx.send(f"♻️ Cleared {len(deleted)} messages")


@client.event
async def on_ready():
    print("Bot ready.")


@client.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client

    if voice_state is None:
        return

    total_members = 0
    for member in voice_state.channel.members:
        if member.id == client.id or not member.bot:
            total_members += 1

    if total_members == 1:
        await voice_state.disconnect()


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
