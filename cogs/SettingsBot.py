import discord
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
    async def settings(self, ctx, *args):
        # TODO SUPPORT MORE THAN BLACKLIST
        if len(args) == 2:
            if args[0].lower() == "blacklist":
                if FireBase.is_in_blacklist(str(ctx.guild.id), str(ctx.channel.id)):
                    await ctx.send(f"`{ctx.channel}` is already in the blacklist")
                else:
                    FireBase.add_text_channel_to_blacklist(
                        str(ctx.guild.id), args[1])
                    await ctx.send(f"Blacklisted `{ctx.channel}`")
