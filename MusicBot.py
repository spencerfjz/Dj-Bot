import re
from youtubesearchpython import VideosSearch
import discord
import asyncio
from discord.ext import commands
from pytube import YouTube
import youtube_dl


def setup(client):
    client.add_cog(MusicBot(client))


class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send(f"You must be in voice channel! {ctx.author.mention}")

        voice_channel = ctx.author.voice.channel

        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)

        await ctx.send(f"👍 **Joined** `{voice_channel.name}`")

    @commands.command()
    async def disconnect(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command(aliases=["stop"])
    async def pause(self, ctx):
        ctx.voice_client.pause()
        await ctx.send("**Paused** ⏸️")

    @commands.command()
    async def resume(self, ctx):
        ctx.voice_client.resume()
        await ctx.send("**Resumed**!")

    @commands.command()
    async def play(self, ctx, *, url):
        print(url)
        await self.join(ctx)
        YDL_OPTIONS = {}
        vc = ctx.voice_client
        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            song_link_regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$"

            await ctx.send(f"🎵 **Searching** 🔎 `{url}`")
            if(not re.match(song_link_regex, url)):
                # Perform search to find video
                videoSearch = VideosSearch(url, limit=1)
                result = videoSearch.result()["result"]
                if(len(result) == 0):
                    print("No videos found when searching")
                    await ctx.send(f"❌ could not find {url}")
                    return
                else:
                    url = result[0]["link"]

            info = ydl.extract_info(url, download=False)
            url2 = info["formats"][0]["url"]
            audio_source = discord.FFmpegPCMAudio(url2)
            print(f"Playing {url}")
            await ctx.send(f"**Playing** 🎶 `{url} -Now!`")
            vc.play(audio_source)
            print(info["title"])
