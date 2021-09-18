import discord
from discord.ext import commands
from wrappers.FireBase import FireBaseContainer


def setup(client):
    client.add_cog(SettingsBot(client))


class SettingsBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.FireBase = FireBaseContainer()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.FireBase.add_new_server(str(guild.id))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.FireBase.remove_server(str(guild.id))

    @commands.Cog.listener()
    async def on_message(self, message):
        message_content = message.content.lower()
        if(message_content[0:9] == "-settings"):
            return
        elif(message_content[0:1] == "-" and self.FireBase.is_in_blacklist(str(message.guild.id), str(message.channel.id))):
            return

    @commands.command()
    async def settings(self, ctx, *args):
        # TODO SUPPORT MORE THAN BLACKLIST
        if len(args) == 2:
            if args[0].lower() == "blacklist":
                self.FireBase.add_text_channel_to_blacklist(
                    str(ctx.guild.id), args[1])
