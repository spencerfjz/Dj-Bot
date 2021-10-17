import discord
import ctypes
import sys
import os
import contextlib
import ctypes.util
import DiscordUtils
from io import StringIO
from discord import colour
from discord import guild
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


async def determine_prefix(bot, message):
    guild_id = SettingsBot.FireBase.retrieve_prefix(str(message.guild.id))
    return guild_id


client = commands.Bot(command_prefix=determine_prefix,
                      intents=discord.Intents.all(), help_command=None)

for cog in cogs:
    cog.setup(client)


@client.command(aliases=["prune", "clean"])
async def purge(ctx):
    deleted = await ctx.channel.purge(limit=100, check=lambda m: m.author == client.user)
    await ctx.send(f"♻️ Cleared {len(deleted)} messages")


@client.command(aliases=["purgeme"])
async def cleanseme(ctx): 
    deleted = await ctx.channel.purge(limit=100, check=lambda m: m.author.id == ctx.author.id)
    await ctx.send(f"♻️ Cleared {len(deleted)} messages by {ctx.author}")

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old


@client.command()
async def code(ctx, *, code):
    try:
        code = code.replace('`', '')
        with stdoutIO() as s:
            exec(code)
        result = s.getvalue()
        if len(result) != 0:
            paginator = DiscordUtils.Pagination.CustomEmbedPaginator(
                ctx, remove_reactions=True, timeout=600)
            paginator.add_reaction('⏮️', "first")
            paginator.add_reaction('⏪', "back")
            paginator.add_reaction('⏩', "next")
            paginator.add_reaction('⏭️', "last")
            code_list = [result[i:i+600] for i in range(0, len(result), 600)]
            embeds = []
            for count, code_set in enumerate(code_list):
                embed = discord.Embed(color=discord.Colour.green()).add_field(
                    name=f"Source Code Output: ", value=f"Page {count+1}")
                embed.add_field(name=f"`Output:`",
                                value=code_set, inline=False)
                embeds.append(embed)

            if len(embeds) == 1:
                await ctx.send(embed=embeds[0])
            else:
                await paginator.run(embeds)
        else:
            await ctx.send("**Code executed.**")
    except Exception as e:
        await ctx.send(e)


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


@client.command()
async def help(ctx):
    print("Reached help message")
    guild_prefix = SettingsBot.FireBase.retrieve_prefix(str(ctx.guild.id))
    embed = discord.Embed(
        title="**Bootleg Rhythm Bot Help Page**",
        description=f"ℹ️ In order to use Bootleg Rhythm, use the prefix `{guild_prefix}` followed by the desired command",
        colour=discord.Colour.red())

    embed.add_field(name="**▶️ Play **",
                    value=f"``{guild_prefix}play [youtube-link | spotify-link | query]``", inline=True)
    embed.add_field(name="**⏸️ Pause **",
                    value=f"``{guild_prefix}pause``", inline=True)
    embed.add_field(name="**⏯️ Resume**",
                    value=f"``{guild_prefix}resume``", inline=True)

    embed.add_field(name="**🔨 Remove from Queue**",
                    value=f"``{guild_prefix}remove [Index]``", inline=True)

    embed.add_field(name="**🧾 Show Queue**",
                    value=f"``{guild_prefix}queue``", inline=True)

    embed.add_field(name="**🎶 Lyrics**",
                    value=f"``{guild_prefix}lyrics``", inline=True)

    embed.add_field(name="**🔎 Search Song**",
                    value=f"``{guild_prefix}search [Song]``", inline=True)

    embed.add_field(name="**📟 Show Current Song**",
                    value=f"``{guild_prefix}current``", inline=True)

    embed.add_field(name="**🆑 Clear Queue**",
                    value=f"``{guild_prefix}clear``", inline=True)

    embed.add_field(name="**⏩ Skip to Position in Queue**",
                    value=f"``{guild_prefix}skipto [Position]``", inline=True)

    embed.add_field(name="**⏭️ Skip to Next Item in Queue**",
                    value=f"``{guild_prefix}next``", inline=True)

    embed.add_field(name="**🔀 Shuffle Queue**",
                    value=f"``{guild_prefix}shuffle``", inline=True)

    embed.add_field(name="**🤖 Join Voice Channel**",
                    value=f"``{guild_prefix}join``", inline=True)

    embed.add_field(name="**🥺 Disconnect from Voice Channel**",
                    value=f"``{guild_prefix}disconnect``", inline=True)

    embed.add_field(name="**⚙️ Access Settings**",
                    value=f"``{guild_prefix}settings``", inline=True)

    await ctx.send(embed=embed)


@client.event
async def on_ready():
    print("Rhythm bot here for da beats.")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="da tunes 🎵"))


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
