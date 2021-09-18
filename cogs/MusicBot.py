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
from cogs.SettingsBot import FireBase
import DiscordUtils

FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


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

            with youtube_dl.YoutubeDL({}) as ydl:
                info = ydl.extract_info(player, download=False)
                url2 = info["formats"][0]["url"]
                # Linux
                audio_source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTS)

                # WINDOWS
                # audio_source = discord.FFmpegPCMAudio(
                #     url2, executable="ffmpeg.exe")

                self.players[id] = audio_source
                print(f"Playing next song from queue")

                vc = ctx.voice_client

                vc.play(audio_source, after=lambda event: self.check_queue(
                    ctx, ctx.guild.id))

    @commands.command(aliases=["now", "playing"])
    async def current(self, ctx):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        # TODO USE EMBED
        # await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command()
    async def clear(self, ctx):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        if ctx.guild.id not in self.queues or len(self.queues[ctx.guild.id]) == 0:
            # TODO: USE EMBED
            await ctx.send("**Queue** is empty")
        else:
            await ctx. send("💥 **Cleared...** ⏹")
            self.queues.clear()

    @commands.command(aliases=["continue", "skip", "fs"])
    async def next(self, ctx):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) != 0:
            url = self.queues[ctx.guild.id][0][0]
            result = VideosSearch(url).result()["result"][0]
            info = {
                "duration": result["duration"],
                "title": result["title"],
                "thumbnail": result["thumbnails"][0]["url"],
            }
            await ctx.send("⏩ **Skipped** 👍")
            await ctx.send(embed=self.build_youtube_embed(ctx, info))
            ctx.voice_client.stop()
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        else:
            await ctx.send(f"Queue is **EMPTY**")

    @commands.command(aliases=["summon"])
    async def join(self, ctx):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

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
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        self.queues.pop(ctx.guild.id, None)
        await ctx.voice_client.disconnect()

    @commands.command()
    async def shuffle(self, ctx):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) != 0:
            random.shuffle(self.queues[ctx.guild.id])
            await ctx.send(f"**Shuffled queue** 👌")
        else:
            await ctx.send(f"Queue is **EMPTY**")

    @commands.command(aliases=["stop"])
    async def pause(self, ctx):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        ctx.voice_client.pause()
        await ctx.send("**Paused** ⏸️")

    @commands.command()
    async def resume(self, ctx):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        ctx.voice_client.resume()
        await ctx.send("**Resumed**!")

    @commands.command(aliases=["queue"])
    async def chain(self, ctx):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        if ctx.guild.id not in self.queues or len(self.queues[ctx.guild.id]) == 0:
            await ctx.send("**Queue** is empty 🗍")
        else:
            paginator = DiscordUtils.Pagination.CustomEmbedPaginator(
                ctx, remove_reactions=True)
            paginator.add_reaction('⏮️', "first")
            paginator.add_reaction('⏪', "back")
            paginator.add_reaction('⏩', "next")
            paginator.add_reaction('⏭️', "last")
            embeds = []
            list_of_songs = []
            main_counter = 1
            list_of_output_strings = []
            for count, info in enumerate(self.queues[ctx.guild.id]):
                title = info[1]
                list_of_songs.append(f"```yaml\n{count+1}: {title}```")
                if main_counter == 10:
                    list_of_output_strings.append('\n'.join(list_of_songs))
                    list_of_songs.clear()
                    main_counter = 0
                main_counter += 1

            for count, output_string in enumerate(list_of_output_strings):
                embed = discord.Embed(color=ctx.author.color).add_field(
                    name=f"Queue for {ctx.guild}", value=f"Page {count+1}")
                embed.add_field(name=f"`Songs:`",
                                value=output_string, inline=False)
                embeds.append(embed)
            await paginator.run(embeds)

    def build_youtube_embed(self, ctx, info):
        duration = info["duration"]
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

        next_song = self.queues[ctx.guild.id][1][1] if ctx.guild.id in self.queues and len(
            self.queues[ctx.guild.id]) != 1 else "Nothing"

        embed.add_field(
            name=f"`Up Next:`", value=next_song, inline=False)

        return embed

    def build_blacklist_embed(self, channel_name):
        embed = discord.Embed(
            title=f"❌ **{channel_name}** is blacklisted.",
            deescription="blacklist_message",
            colour=discord.Colour.dark_red()
        )

        return embed

    @commands.command(aliases=["add", "playnext"])
    async def play(self, ctx, *, url):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        await self.join(ctx)
        YDL_OPTIONS = {}
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
                    video_urls = list(playlist.videos)
                    print(f"{len(video_urls)} items in playlist")
                    url = video_urls[0].watch_url
                    for index in range(1, len(video_urls)):
                        link = video_urls[index].watch_url
                        title = video_urls[index].title
                        if ctx.guild.id in self.queues:
                            self.queues[ctx.guild.id].append((link, title))
                        else:
                            self.queues[ctx.guild.id] = [(link, title)]

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
        vc = ctx.voice_client

        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            song_link_regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$"
            youtube_playlist_regex = r"^.*(youtu.be\/|list=)([^#\&\?]*).*"
            await ctx.send(f"🎵 **Searching** 🔎 `{url}`")
            if(re.match(youtube_playlist_regex, url)):
                await ctx.send(f"**Queued** 🎤 `{url}`")
                playlist = Playlist(url)
                video_urls = list(playlist.videos)
                for index in range(1, len(video_urls)):
                    link = video_urls[index].watch_url
                    title = video_urls[index].title
                    if ctx.guild.id in self.queues:
                        self.queues[ctx.guild.id].append((link, title))
                    else:
                        self.queues[ctx.guild.id] = [(link, title)]
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

            guild_id = ctx.guild.id
            title = VideosSearch(url, limit=1).result()[
                "result"][0]["title"]
            self.players[guild_id] = url
            if guild_id in self.queues:
                self.queues[guild_id].append((url, title))
            else:
                self.queues[guild_id] = [(url, title)]

            await ctx.send(f"**Queued** 🎤 `{url}`")
