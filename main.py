import discord
import ctypes
import sys
import os
import ctypes.util
from discord.ext import commands
from discord.errors import ClientException
from discord_components import Button, ButtonStyle
import cogs.MusicBot as MusicBot
import cogs.SettingsBot as SettingsBot


# Following three lines @Linux
opus = ctypes.util.find_library('opus')
discord.opus.load_opus(opus)
discord.opus.is_loaded()

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")


cogs = [MusicBot, SettingsBot]
intents = discord.Intents.all()
intents.members = True
client = commands.Bot(command_prefix="-", intents=discord.Intents.all())

for cog in cogs:
    cog.setup(client)


@client.command(aliases=["prune", "clean"])
async def purge(ctx):
    deleted = await ctx.channel.purge(limit=100, check=lambda m: m.author == client.user)
    await ctx.send(f"♻️ Cleared {len(deleted)} messages")


@client.command()
async def ping(ctx):
    if round(client.latency * 1000) <= 50:
        embed = discord.Embed(
            title="PING", description=f":ping_pong: My ping is **{round(client.latency *1000)}** ms.", color=0x44ff44)
    elif round(client.latency * 1000) <= 100:
        embed = discord.Embed(
            title="PING", description=f":ping_pong: My ping is **{round(client.latency *1000)}** ms.", color=0xffd000)
    elif round(client.latency * 1000) <= 200:
        embed = discord.Embed(
            title="PING", description=f":ping_pong: My ping is **{round(client.latency *1000)}** ms.", color=0xff6600)
    else:
        embed = discord.Embed(
            title="PING", description=f":ping_pong: My ping is **{round(client.latency *1000)}** ms.", color=0x990000)
    await ctx.send(embed=embed)


@client.event
async def on_ready():
    print("Rhythm bot here for da beats.")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Da Tunes 🎵"))


@client.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client

    if voice_state is None:
        return

    total_members = 0
    for member in voice_state.channel.members:
        if str(member.id) == "877284062954389605" or not member.bot:
            total_members += 1

    if total_members == 1:
        print("Leaving empty voice channel.")
        await voice_state.disconnect()


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
