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
        FireBase.add_new_server(str(guild.id))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        FireBase.remove_server(str(guild.id))

    @commands.command()
    async def prefix(self, ctx, prefix):
        guild_id = str(ctx.guild.id)
        FireBase.update_prefix(guild_id, prefix)
        await ctx.send(f"👍 **Prefix set to {prefix}**")

    @commands.command()
    async def blacklist(self, ctx, arg):
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
            deescription="reset_message",
            colour=discord.Colour.dark_gray()
        )
        await ctx.send(embed=embed)
