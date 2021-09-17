import re
import random
import time
from sys import executable
from youtubesearchpython import VideosSearch
import discord
import asyncio
from discord.ext import commands
from pytube import YouTube, Playlist
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

            vc = ctx.voice_client

            # Linux
            vc.play(player, after=lambda event: self.check_queue(
                ctx, ctx.guild.id))

    @commands.command(aliases=["now", "playing"])
    async def current(self, ctx):
        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command
    async def clear(self, ctx):
        if ctx.guild.id not in self.queues or len(self.queues[ctx.guild.id]) == 0:
            # TODO: USE EMBED
            await ctx.send("**Queue** is empty")
        else:
            await ctx. send("**Queue** is cleared!")
            self.queues.clear()

    @commands.command(aliases=["continue", "skip"])
    async def next(self, ctx):
        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) != 0:
            info = self.queues[ctx.guild.id][0][1]
            recent_song = info["title"]
            await ctx.send(f"**Now playing** 🎶 `{recent_song}`")
            await ctx.send(embed=self.build_youtube_embed(ctx, info))
            await ctx.voice_client.stop()
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        else:
            await ctx.send(f"Queue is **EMPTY**")

    @commands.command(aliases=["summon"])
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send(f"You must be in voice channel! {ctx.author.mention}")

        voice_channel = ctx.author.voice.channel

        if ctx.voice_client is None:
            await voice_channel.connect()
            await ctx.send(f"👍 **Joined** `{voice_channel.name}`")
        else:
            await ctx.voice_client.move_to(voice_channel)

    @commands.command(aliases=["leave", "quit", "exit"])
    async def disconnect(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def shuffle(self, ctx):
        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) != 0:
            random.shuffle(self.queues[ctx.guild.id])
            await ctx.send(f"**Shuffled queue** 👌")
        else:
            await ctx.send(f"Queue is **EMPTY**")

    @commands.command(aliases=["stop"])
    async def pause(self, ctx):
        ctx.voice_client.pause()
        await ctx.send("**Paused** ⏸️")

    @commands.command()
    async def resume(self, ctx):
        ctx.voice_client.resume()
        await ctx.send("**Resumed**!")

    @commands.command(aliases=["queue"])
    async def chain(self, ctx):
        if ctx.guild.id not in self.queues or len(self.queues[ctx.guild.id]) == 0:
            await ctx.send("**Queue** is empty 🗍")
        else:
            list_of_songs = []
            for count, song in enumerate(self.queues[ctx.guild.id]):
                title = song[1]["title"]
                list_of_songs.append(f"{count+1}: {title}")

            output_string = '\n'.join(list_of_songs)
            await ctx.send(f"```yaml\n{output_string}```")

    def build_youtube_embed(self, ctx, info):
        duration = time.strftime("%M:%S", time.gmtime(info["duration"]))
        title = info["title"]
        author_name = ctx.message.author.name if ctx.message else None
        thumbnail = info["thumbnail"]

        embed = discord.Embed(
            title="Now Playing 🎵",
            description=title,
            colour=discord.Colour.blue()
        )
        embed.set_thumbnail(url=thumbnail)
        embed.add_field(
            name=f"`Length:`", value=duration, inline=False)

        if author_name is not None:
            embed.add_field(
                name=f"`Requested by:`", value=author_name, inline=False)

        next_song = self.queues[ctx.guild.id][1][1]["title"] if ctx.guild.id in self.queues and len(
            self.queues[ctx.guild.id]) != 1 else "Nothing"

        embed.add_field(
            name=f"`Up Next:`", value=next_song, inline=False)

        return embed

    @commands.command(aliases=["add", "playnext"])
    async def play(self, ctx, *, url):
        await self.join(ctx)
        YDL_OPTIONS = {}
        FFMPEG_OPTS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        vc = ctx.voice_client

        if vc.is_playing():
            await self.queue(ctx, url)
        else:
            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                youtube_video_regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$"
                youtube_playlist_regex = r"^.*(youtu.be\/|list=)([^#\&\?]*).*"
                await ctx.send(f"🎵 **Searching** 🔎 `{url}`")
                if(re.match(youtube_playlist_regex, url)):
                    playlist = Playlist(url)
                    url = playlist.video_urls[0]
                    for index in range(1, len(playlist.video_urls)):
                        link = playlist.video_urls[index]
                        info = ydl.extract_info(link, download=False)
                        url2 = info["formats"][0]["url"]
                        audio_source = discord.FFmpegPCMAudio(
                            url2, **FFMPEG_OPTS)
                        if ctx.guild.id in self.queues:
                            self.queues[ctx.guild.id].append(
                                (audio_source, info))
                        else:
                            self.queues[ctx.guild.id] = [(audio_source, info)]

                elif(not re.match(youtube_video_regex, url)):
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
                audio_source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTS)

                # WINDOWS
                # audio_source = discord.FFmpegPCMAudio(
                #     url2, executable="ffmpeg.exe")

                print(f"Playing {url}")

                embed = self.build_youtube_embed(ctx, info)

                await ctx.send(f"**Playing** 🎶 `{url} - Now!`")
                await ctx.send(embed=embed)

                self.players[ctx.guild.id] = audio_source
                vc.play(audio_source, after=lambda event: self.check_queue(
                    ctx, ctx.guild.id))

    async def queue(self, ctx, url):
        print(f"Queueing {url}")
        await self.join(ctx)
        YDL_OPTIONS = {}
        FFMPEG_OPTS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        vc = ctx.voice_client

        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            song_link_regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$"
            youtube_playlist_regex = r"^.*(youtu.be\/|list=)([^#\&\?]*).*"
            await ctx.send(f"🎵 **Searching** 🔎 `{url}`")
            if(re.match(youtube_playlist_regex, url)):
                await ctx.send(f"**Queued** 🎤 `{url}`")
                playlist = Playlist(url)
                for index in range(1, len(playlist.video_urls)):
                    link = playlist.video_urls[index]
                    info = ydl.extract_info(link, download=False)
                    url2 = info["formats"][0]["url"]
                    audio_source = discord.FFmpegPCMAudio(
                        url2, **FFMPEG_OPTS)
                    if ctx.guild.id in self.queues:
                        self.queues[ctx.guild.id].append(
                            (audio_source, info))
                    else:
                        self.queues[ctx.guild.id] = [(audio_source, info)]
                return
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
            audio_source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTS)

            # WINDOWS
            # audio_source = discord.FFmpegPCMAudio(
            #     url2, executable="ffmpeg.exe")

            guild_id = ctx.guild.id

            if guild_id in self.queues:
                self.queues[guild_id].append((audio_source, info))
            else:
                self.queues[guild_id] = [(audio_source, info)]

            await ctx.send(f"**Queued** 🎤 `{url}`")
