import re
from sys import executable
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
        self.queues = {}
        self.players = {}
        self.next = asyncio.Event()

    def check_queue(self, ctx, id):
        if id in self.queues and self.queues[id] != []:
            player = self.queues[id].pop(0)[0]
            self.players[id] = player
            print(f"Playing next song from queue")

            print(player)
            # Linux
            vc = ctx.voice_client
            vc.play(player, after=lambda event: self.check_queue(
                ctx, ctx.guild.id))

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send(f"You must be in voice channel! {ctx.author.mention}")

        voice_channel = ctx.author.voice.channel

        if ctx.voice_client is None:
            await voice_channel.connect()
            await ctx.send(f"👍 **Joined** `{voice_channel.name}`")
        else:
            await ctx.voice_client.move_to(voice_channel)

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
    async def chain(self, ctx):
        if ctx.guild.id not in self.queues or len(self.queues[ctx.guild.id]) == 0:
            await ctx.send("**Queue** is empty 🗍")
        else:
            list_of_songs = []
            for count, song in enumerate(self.queues[ctx.guild.id]):
                list_of_songs.append(f"{count+1}: {song[1]}")

            output_string = '\n'.join(list_of_songs)
            await ctx.send(f"```yaml\n{output_string}```")

    @commands.command(aliases=["queue"])
    async def play(self, ctx, *, url):
        print(url)
        await self.join(ctx)
        YDL_OPTIONS = {}
        vc = ctx.voice_client

        if vc.is_playing():
            await self.queue(ctx, url)
        else:
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

                # Linux
                FFMPEG_OPTS = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

                audio_source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTS)

            # WINDOWS
            # audio_source = discord.FFmpegPCMAudio(
            #     url2, executable="ffmpeg.exe")

            print(f"Playing {url}")
            await ctx.send(f"**Playing** 🎶 `{url} -Now!`")
            self.players[ctx.guild.id] = audio_source
            vc.play(audio_source, after=lambda event: self.check_queue(
                ctx, ctx.guild.id))
            print(info["title"])

    async def queue(self, ctx, url):
        print("HERE")
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

            # Linux
            FFMPEG_OPTS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

            audio_source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTS)

            # WINDOWS
            # audio_source = discord.FFmpegPCMAudio(
            #     url2, executable="ffmpeg.exe")

            guild_id = ctx.guild.id

            if guild_id in self.queues:
                self.queues[guild_id].append((audio_source, url))
            else:
                self.queues[guild_id] = [(audio_source, url)]

            await ctx.send(f"**Queued** 🎤 `{url}`")
