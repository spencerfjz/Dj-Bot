import discord
import re
from discord.ext import commands
from wrappers.FireBase import FireBaseContainer

FireBase = FireBaseContainer()


def setup(client):
    client.add_cog(SettingsBot(client))


class SettingsBot(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if len(guild.text_channels) > 0:
            channel = self.client.get_channel(guild.text_channels[0].id)
            await channel.send("**Thank you for adding me!** ✅")
            await channel.send("`-` My prefix here is `-`")
            await channel.send("`-` You can change my prefix with `-prefix <prefix>`")

        FireBase.add_new_server(str(guild.id))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        FireBase.remove_server(str(guild.id))

    @commands.command()
    async def prefix(self, ctx, prefix=None):
        if prefix is None or len(prefix) > 5:
            error_message = "No prefix given!" if prefix is None else "Prefix must be at most 5 characters (e.g. !)"
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                description=error_message,
                colour=discord.Colour.dark_red()
            )
            await ctx.send(embed=embed)
        else:
            guild_id = str(ctx.guild.id)
            FireBase.update_prefix(guild_id, prefix)
            await ctx.send(f"👍 **Prefix set to** `{prefix}`")

    @commands.command()
    async def announcesongs(self, ctx, setting=None):
        if setting is None or (setting.lower() != "on" and setting.lower() != "off"):
            error_message = "No setting provided!" if setting is None else "Setting must be either on or off (e.g. [on | off])"
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                description=error_message,
                colour=discord.Colour.dark_red()
            )
            await ctx.send(embed=embed)
        else:
            desired_setting = True if setting.lower() == "on" else False
            FireBase.update_announce_songs_settings(
                str(ctx.guild.id), desired_setting)

            action_string = "now" if desired_setting else "not"
            await ctx.send(f"**✅ I will {action_string} announce new songs.**")

    @commands.command()
    async def blacklist(self, ctx, arg=None):
        if arg is None:
            embed = discord.Embed(
                title=f"❌ **Invalid usage**",
                description="Must mention a text channel!",
                colour=discord.Colour.dark_red()
            )
            await ctx.send(embed=embed)
        else:
            text_channel = arg.replace("<#", "")
            text_channel = text_channel.replace(">", "")
            num_regex = r"[0-9]+"
            if not re.match(num_regex, text_channel):
                text_channel = "0"

            channel = self.client.get_channel(int(text_channel))
            if channel is None:
                await ctx.send(f"Invalid channel mention given, use the following format `-blacklist <channel_id>`")
            elif FireBase.is_in_blacklist(str(ctx.guild.id), str(channel.id)):
                await ctx.send(f"`{channel.name}` is already in the blacklist")
            else:
                FireBase.add_text_channel_to_blacklist(
                    str(ctx.guild.id), str(channel.id))
                await ctx.send(f"Blacklisted `{channel.name}`")

    @commands.command()
    async def reset(self, ctx):
        FireBase.remove_server(str(ctx.guild.id))
        FireBase.add_new_server(str(ctx.guild.id))
        embed = discord.Embed(
            title=f"♻️ Reset settings for **{ctx.guild}**",
            colour=discord.Colour.dark_gray()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def settings(self, ctx, arg=None):
        guild_prefix = FireBase.retrieve_prefix(str(ctx.guild.id))
        # Settings Message Case
        if arg is None:
            embed = discord.Embed(
                title="**Bootleg Rhythm Settings**",
                description=f"Use the command format `{guild_prefix}settings <option>` to view more info about an option.",
                color=0x000000
            )
            embed.add_field(
                name="❗ **Prefix**", value=f"`{guild_prefix}settings prefix`", inline=True)

            embed.add_field(
                name="🚫 **Blacklist**", value=f"`{guild_prefix}settings blacklist`", inline=True)

            embed.add_field(
                name="♻️ **Reset**", value=f"`{guild_prefix}settings reset`", inline=True)

            embed.add_field(
                name="🔔 **Announce Songs**", value=f"`{guild_prefix}settings announcesongs`", inline=False)

            await ctx.send(embed=embed)
        elif arg == "prefix":
            embed = discord.Embed(
                title="**Bootleg Rhythm Settings -** ❗**Prefix**",
                description="Changes the prefix used to address Bootleg Rhythm bot.",
                color=0x000000
            )

            embed.add_field(name="📄 **Current Setting:**",
                            value=f"`{guild_prefix}`", inline=False)

            embed.add_field(
                name="✏️ **Update:**", value=f"`{guild_prefix}prefix [New Prefix]`", inline=False)

            embed.add_field(name="✅ **Valid Settings:**",
                            value="`Any text, at most 5 characters (e.g. !)`", inline=False)

            await ctx.send(embed=embed)

        elif arg == "blacklist":
            embed = discord.Embed(
                title="**Bootleg Rhythm Settings - ** 🚫 **Blacklist**",
                description="Prevents a text channel from using dj commands.",
                color=0x000000
            )

            embed.add_field(
                name="✏️ **Update:**", value=f"`{guild_prefix}blacklist #channel_name`", inline=False)

            embed.add_field(name="✅ **Valid Settings:**",
                            value="`Must mention a text channel`", inline=False)

            await ctx.send(embed=embed)

        elif arg == "reset":
            embed = discord.Embed(
                title="**Bootleg Rhythm Settings - ** ♻️ **Reset**",
                description="Resets server settings back to default (e.g. reset blacklist & prefix)",
                color=0x000000
            )
            await ctx.send(embed=embed)
        elif arg == "announcesongs":
            announce_song_settings = "on" if FireBase.retrieve_announce_songs_settings(
                str(ctx.guild.id)) else "off"

            embed = discord.Embed(
                title="**Bootleg Rhythm Settings - ** 🔔 **Announce Songs**",
                description="Sets whether or not songs are announced as they are played.",
                color=0x000000
            )

            embed.add_field(name="📄 **Current Setting:**",
                            value=f"`{announce_song_settings}`", inline=False)
            embed.add_field(
                name="✏️ **Update:**", value=f"`{guild_prefix}announcesong [on | off]`", inline=False)

            embed.add_field(name="✅ **Valid Settings:**",
                            value="`on or off only`", inline=False)
            await ctx.send(embed=embed)
