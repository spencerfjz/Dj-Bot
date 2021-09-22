import re
import random
import wrappers.Spotify as Spotify
import time
import os
from sys import executable
import constants
from youtubesearchpython import VideosSearch, CustomSearch, VideoSortOrder
import discord
import asyncio
from discord.ext import commands
from pytube import YouTube, Playlist
import youtube_dl
from cogs.SettingsBot import FireBase
import DiscordUtils
import lyricsgenius as lg


genius_api = lg.Genius(os.environ.get("GENIUS_KEY"), skip_non_songs=True, excluded_terms=[
                       "(Remix)", "(Live)"], remove_section_headers=False)

FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


def setup(client):
    client.add_cog(MusicBot(client))


class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.current_track = {}
        self.queues = {}
        self.players = {}

    def check_queue(self, ctx, id):
        if id in self.queues and self.queues[id] != []:
            queue_item = self.queues[id].pop(0)
            player = queue_item[0]

            if player == constants.SPOTIFY_PLAYLIST_ITEM:
                videoSearch = VideosSearch(queue_item[1], limit=1)
                result = videoSearch.result()["result"]
                if(len(result) == 0):
                    self.check_queue(ctx, ctx.guild.id)
                else:
                    player = result[0]["link"]

            with youtube_dl.YoutubeDL({}) as ydl:
                info = ydl.extract_info(player, download=False)
                url2 = info["formats"][0]["url"]
                # Linux
                audio_source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTS)

                # WINDOWS
                # audio_source = discord.FFmpegPCMAudio(
                # url2, executable="ffmpeg.exe", **FFMPEG_OPTS)

                self.players[id] = audio_source
                print(f"Playing next song from queue")

                vc = ctx.voice_client
                self.current_track[ctx.guild.id] = info
                announce_songs_settings = FireBase.retrieve_announce_songs_settings(
                    str(ctx.guild.id))
                if announce_songs_settings:
                    self.client.loop.create_task(
                        ctx.send(embed=self.build_youtube_embed(ctx, info)))
                vc.play(audio_source, after=lambda event: self.check_queue(
                    ctx, ctx.guild.id))
        else:
            self.current_track.pop(ctx.guild.id, None)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_state = member.guild.voice_client

        if voice_state is None:
            return

        total_members = 0
        for member in voice_state.channel.members:
            if str(member.id) == str(self.client.user.id) or not member.bot:
                total_members += 1

        if total_members == 1:
            print("Leaving empty voice channel.")
            self.queues.pop(member.guild.id, None)
            await voice_state.disconnect()

    @commands.command(aliases=["lookup"])
    async def search(self, ctx, *, search_argument=None):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return
        elif search_argument is None:
            guild_prefix = FireBase.retrieve_prefix(str(ctx.guild.id))
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                description=f"{guild_prefix}search [query]",
                colour=discord.Colour.dark_red()
            )
            await ctx.send(embed=embed)
            return

        search_results = CustomSearch(
            query=search_argument, limit=10, searchPreferences=VideoSortOrder.viewCount).result()["result"]

        if(len(search_results) == 0):
            await ctx.send(f"❌ could not find {search_argument}")
        else:
            embed = discord.Embed(
                title=f"**🔎 Search Results for: {search_argument}**",
                colour=0x000000,
            )

            output_list = []
            for count, item in enumerate(search_results):
                url = item["link"]
                title = item["title"]
                duration = item["duration"]
                output_list.append(
                    f"`{count+1}.` [{title}]({url}) **[{duration}]**")

            embed = discord.Embed(
                title=f"**🔎 Search Results for: {search_argument}**",
                description="\n\n".join(output_list),
                colour=0x000000,

            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(aliases=["now", "playing"])
    async def current(self, ctx):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        if ctx.guild.id in self.current_track:
            await ctx.send(embed=self.build_youtube_embed(ctx, self.current_track[ctx.guild.id]))
        else:
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                deescription="invalid_usage_message",
                colour=discord.Colour.dark_red()
            )
            embed.add_field(name="`Error:`",
                            value="No song currently playing", inline=False)
            await ctx.send(embed=embed)

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
            self.queues.pop(ctx.guild.id, None)

    def is_valid_index(self, ctx, ind):
        if ind < 0 or ind >= len(self.queues[ctx.guild.id]):
            return False
        else:
            return True

    @commands.command()
    async def skipto(self, ctx, position=None):
        guild_prefix = FireBase.retrieve_prefix(str(ctx.guild.id))
        if position == None or not position.isdigit():
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                description=f"{guild_prefix}skipto [Position]",
                colour=discord.Colour.dark_red()
            )
            await ctx.send(embed=embed)
        elif ctx.guild.id not in self.queues or len(self.queues[ctx.guild.id]) == 0:
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                description=f"Queue is empty",
                colour=discord.Colour.dark_red()
            )
            await ctx.send(embed=embed)
        elif not self.is_valid_index(ctx, int(position)-1):
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                description=f"Invalid position given",
                colour=discord.Colour.dark_red()
            )
            await ctx.send(embed=embed)
        else:
            position = int(position)
            result = self.queues[ctx.guild.id][position -
                                               1:len(self.queues[ctx.guild.id])]
            self.queues.pop(ctx.guild.id, None)
            self.queues[ctx.guild.id] = result
            await self.next(ctx)

    @commands.command(aliases=["continue", "skip", "fs"])
    async def next(self, ctx):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) != 0:
            await ctx.send("⏩ ***Skipped*** 👍")
            ctx.voice_client.stop()
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        else:
            await ctx.send("❌ **Nothing playing in this server**")

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

    @commands.command()
    async def lyrics(self, ctx):
        if ctx.guild.id not in self.current_track:
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                deescription="invalid_usage_message",
                colour=discord.Colour.dark_red()
            )
            embed.add_field(name="`Error:`",
                            value="No song currently playing", inline=False)
            await ctx.send(embed=embed)
        else:
            title = self.current_track[ctx.guild.id]["title"]
            await ctx.send(f"🔎 **Searching lyrics for** `{title}`")
            song_search = genius_api.search_song(title)
            if song_search is None:
                embed = discord.Embed(
                    title=f"😥 **Lyrics Not Found**",
                    deescription="lyrics_not_found_message",
                    colour=discord.Colour.dark_red()
                )
                embed.add_field(name="`Error:`",
                                value=f"No lyrics found for {title}", inline=False)
                await ctx.send(embed=embed)
                return

            lyrics = song_search.lyrics
            paginator = DiscordUtils.Pagination.CustomEmbedPaginator(
                ctx, remove_reactions=True, timeout=600)
            paginator.add_reaction('⏮️', "first")
            paginator.add_reaction('⏪', "back")
            paginator.add_reaction('⏩', "next")
            paginator.add_reaction('⏭️', "last")
            lyrics_list = [lyrics[i:i+600] for i in range(0, len(lyrics), 600)]
            embeds = []
            for count, lyrics_set in enumerate(lyrics_list):
                embed = discord.Embed(color=discord.Colour.green()).add_field(
                    name=f"Lyrics for {title}", value=f"Page {count+1}")
                embed.add_field(name=f"`Lyrics:`",
                                value=lyrics_set, inline=False)
                embeds.append(embed)

            if len(embeds) == 1:
                await ctx.send(embed=embeds[0])
            else:
                await paginator.run(embeds)

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
        elif ctx.author.voice is None:
            await ctx.send(f"You must be in voice channel! {ctx.author.mention}")
        elif ctx.voice_client is None:
            guild_prefix = FireBase.retrieve_prefix(str(ctx.guild.id))
            await ctx.send(f"❌ **I am not connected to a voice channel.** Type `{guild_prefix}join` to get me in one")
        else:
            ctx.voice_client.resume()
            await ctx.send("⏯️ **Resuming** 👍")

    @commands.command(aliases=["r"])
    async def remove(self, ctx, position=None):
        guild_prefix = FireBase.retrieve_prefix(str(ctx.guild.id))
        if position is None or not position.isdigit():
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                description=f"{guild_prefix}remove [Index]",
                colour=discord.Colour.dark_red()
            )
            embed.add_field(name="Example", value=f"`{guild_prefix}remove 1`")
            await ctx.send(embed=embed)
        elif ctx.guild.id not in self.queues or len(self.queues[ctx.guild.id]) == 0:
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                description=f"Queue is empty",
                colour=discord.Colour.dark_red()
            )
            await ctx.send(embed=embed)
        elif not self.is_valid_index(ctx, int(position)-1):
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                description=f"Invalid position given",
                colour=discord.Colour.dark_red()
            )
            await ctx.send(embed=embed)
        else:
            title = self.queues[ctx.guild.id].pop(int(position)-1)[1]
            await ctx.send(f"✅ **Removed** `{title}`")

    @commands.command(aliases=["queue", "q"])
    async def chain(self, ctx):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return

        if ctx.guild.id not in self.queues or len(self.queues[ctx.guild.id]) == 0:
            await ctx.send("**Queue** is empty 🗍")
        else:
            paginator = DiscordUtils.Pagination.CustomEmbedPaginator(
                ctx, remove_reactions=True, timeout=600)
            paginator.add_reaction('⏮️', "first")
            paginator.add_reaction('⏪', "back")
            paginator.add_reaction('⏩', "next")
            paginator.add_reaction('⏭️', "last")
            embeds = []
            list_of_songs = []
            for count, info in enumerate(self.queues[ctx.guild.id]):
                title = info[1]
                list_of_songs.append(f"```yaml\n{count+1}: {title}```")

            songs_list = [list_of_songs[i:i+10]
                          for i in range(0, len(list_of_songs), 10)]

            for count, s_list in enumerate(songs_list):
                embed = discord.Embed(color=ctx.author.color).add_field(
                    name=f"Queue for {ctx.guild}", value=f"Page {count+1}")
                embed.add_field(name=f"`Songs:`",
                                value="".join(s_list), inline=False)
                embeds.append(embed)

            if len(embeds) == 1:
                await ctx.send(embed=embeds[0])
            else:
                await paginator.run(embeds)

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

        next_song = self.queues[ctx.guild.id][0][1] if ctx.guild.id in self.queues and len(
            self.queues[ctx.guild.id]) >= 1 else "Nothing"

        embed.add_field(
            name=f"`Up Next:`", value=next_song, inline=False)

        return embed

    def build_blacklist_embed(self, channel_name):
        embed = discord.Embed(
            title=f"🚫 **{channel_name}** is blacklisted.",
            deescription="blacklist_message",
            colour=discord.Colour.dark_red()
        )

        return embed

    def queueSpotifyPlaylist(self, ctx,  result, start):
        for index in range(start, len(result)):
            track = result[index]
            if ctx.guild.id in self.queues:
                self.queues[ctx.guild.id].append(
                    (constants.SPOTIFY_PLAYLIST_ITEM, track, "filler"))
            else:
                self.queues[ctx.guild.id] = [
                    (constants.SPOTIFY_PLAYLIST_ITEM, track, "filler")]

    @commands.command(aliases=["add", "playnext", "p"])
    async def play(self, ctx, *, url=None):
        if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
            await ctx.send(embed=self.build_blacklist_embed(ctx.channel))
            return
        elif url is None:
            guild_prefix = FireBase.retrieve_prefix(str(ctx.guild.id))
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                description=f"{guild_prefix}play [Link or query]",
                colour=discord.Colour.dark_red()
            )
            await ctx.send(embed=embed)
            return

        await self.join(ctx)
        YDL_OPTIONS = {}
        vc = ctx.voice_client

        if vc.is_playing():
            await self.queue(ctx, url)
        else:
            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                await ctx.send(f"🎵 **Searching** 🔎 `{url}`")

                if(re.match(constants.SPOTIFY_ALBUM_REGEX, url)):
                    spotify_album_list = Spotify.getAlbum(url)
                    if spotify_album_list is None:
                        print("No videos found when searching")
                        await ctx.send(f"❌ could not find {url}")
                        return

                    url = spotify_album_list[0]
                    video_search = VideosSearch(url, limit=1)
                    video_search_result = video_search.result()["result"]
                    if(len(video_search_result) == 0):
                        print("No videos found when searching")
                        await ctx.send(f"❌ could not find {url}")
                        return
                    else:
                        url = video_search_result[0]["link"]

                    self.queueSpotifyPlaylist(ctx, spotify_album_list, 1)
                elif (re.match(constants.SPOTIFY_TRACK_REGEX, url)):
                    spotify_track = Spotify.getSong(url)
                    if spotify_track is None:
                        print("No videos found when searching")
                        await ctx.send(f"❌ could not find {url}")
                        return
                    else:
                        videoSearch = VideosSearch(spotify_track, limit=1)
                        result = videoSearch.result()["result"]
                        if(len(result) == 0):
                            print("No videos found when searching")
                            await ctx.send(f"❌ could not find {url}")
                            return
                        else:
                            url = result[0]["link"]

                elif (re.match(constants.SPOTIFY_PLAYLIST_REGEX, url)):
                    try:
                        result = Spotify.getTracks(url)
                        url = result[0]
                        video_search = VideosSearch(url, limit=1)
                        video_search_result = video_search.result()["result"]
                        if(len(video_search_result) == 0):
                            print("No videos found when searching")
                            await ctx.send(f"❌ could not find {url}")
                            return
                        else:
                            url = video_search_result[0]["link"]

                        self.queueSpotifyPlaylist(ctx, result, 1)

                    except Exception as ex:
                        print(ex)
                        print("No videos found when searching")
                        await ctx.send(f"❌ could not find {url}")
                        return
                elif(re.match(constants.YOUTUBE_PLAYLIST_REGEX, url)):
                    playlist = Playlist(url)
                    video_urls = list(playlist.videos)
                    print(f"{len(video_urls)} items in playlist")
                    url = video_urls[0].watch_url
                    for index in range(1, len(video_urls)):
                        link = video_urls[index].watch_url
                        title = video_urls[index].title
                        if ctx.guild.id in self.queues:
                            self.queues[ctx.guild.id].append(
                                (link, title, constants.YOUTUBE_PLAYLIST_ITEM))
                        else:
                            self.queues[ctx.guild.id] = [
                                (link, title, constants.YOUTUBE_PLAYLIST_ITEM)]

                elif(not re.match(constants.YOUTUBE_VIDEO_REGEX, url)):
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
                # url2, executable="ffmpeg.exe", **FFMPEG_OPTS)

                print(f"Playing {url}")

                embed = self.build_youtube_embed(ctx, info)
                title = info["title"]
                announce_songs_settings = FireBase.retrieve_announce_songs_settings(
                    str(ctx.guild.id))
                if announce_songs_settings:
                    await ctx.send(f"**Playing** 🎶 `{title} - Now!`")
                    await ctx.send(embed=embed)

                self.players[ctx.guild.id] = audio_source
                self.current_track[ctx.guild.id] = info
                vc.play(audio_source, after=lambda event: self.check_queue(
                    ctx, ctx.guild.id))

    async def queue(self, ctx, url):
        print(f"Queueing {url}")
        await self.join(ctx)
        await ctx.send(f"🎵 **Searching** 🔎 `{url}`")

        if(re.match(constants.SPOTIFY_ALBUM_REGEX, url)):
            spotify_album_list = Spotify.getAlbum(url)
            if spotify_album_list is None:
                print("No videos found when searching")
                await ctx.send(f"❌ could not find {url}")
                return
            self.queueSpotifyPlaylist(ctx, spotify_album_list, 0)
            await ctx.send(f"**Queued** 🎤 `{url}`")
            return
        elif (re.match(constants.SPOTIFY_TRACK_REGEX, url)):
            spotify_track = Spotify.getSong(url)
            if spotify_track is None:
                print("No videos found when searching")
                await ctx.send(f"❌ could not find {url}")
                return
            else:
                videoSearch = VideosSearch(spotify_track, limit=1)
                result = videoSearch.result()["result"]
                if(len(result) == 0):
                    print("No videos found when searching")
                    await ctx.send(f"❌ could not find {url}")
                    return
                else:
                    url = result[0]["link"]
        elif(re.match(constants.SPOTIFY_PLAYLIST_REGEX, url)):
            try:
                result = Spotify.getTracks(url)
                self.queueSpotifyPlaylist(ctx, result, 0)
                await ctx.send(f"**Queued** 🎤 `{url}`")
            except Exception as ex:
                print("No videos found when searching")
                await ctx.send(f"❌ could not find {url}")
            return
        elif(re.match(constants.YOUTUBE_PLAYLIST_REGEX, url)):
            await ctx.send(f"**Queued** 🎤 `{url}`")
            playlist = Playlist(url)
            video_urls = list(playlist.videos)
            for index in range(1, len(video_urls)):
                link = video_urls[index].watch_url
                title = video_urls[index].title
                if ctx.guild.id in self.queues:
                    self.queues[ctx.guild.id].append(
                        (link, title, constants.YOUTUBE_PLAYLIST_ITEM))
                else:
                    self.queues[ctx.guild.id] = [
                        (link, title, constants.YOUTUBE_PLAYLIST_ITEM)]
            return
        elif(not re.match(constants.YOUTUBE_VIDEO_REGEX, url)):
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
            self.queues[guild_id].append(
                (url, title, constants.YOUTUBE_ITEM))
        else:
            self.queues[guild_id] = [(url, title, constants.YOUTUBE_ITEM)]

        await ctx.send(f"**Queued** 🎤 `{title}`")
