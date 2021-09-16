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


@client.event
async def on_voice_state_update(member, before, after):
    isEmptyServer = before.channel is not None and len(
        before.channel.members) == 1

    if(isEmptyServer):
        if(member.guild.voice_client is not None):
            print("Disconnecting from empty voice channel")
            text_channels = member.guild.text_channels
            text_channel_id = text_channels[0].id
            if text_channel_id is not None:
                channel = client.get_channel(text_channel_id)
                await channel.send(f"**Disconnecting!** ...")

            await member.guild.voice_client.disconnect()


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)