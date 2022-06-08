from disnake.ext import commands, tasks
from bot.exceptions import TaskExists, TaskDoesNotExist
from bot.db import ToDoListManager, SettingsManager
import logging
import disnake
from pprint import pprint
from datetime import timedelta

log = logging.getLogger(__name__)


class Settings(commands.Cog):
    """Contains the cmds related to bot settings."""

    def __init__(self, bot):
        self.bot = bot
        self.connect_settings.start()

    def is_guild_owner():
        async def predicate(ctx):
            return (
                ctx.guild.owner_id == ctx.author.id
                or ctx.author.guild_permissions.administrator
            )

        return commands.check(predicate)

    @tasks.loop(count=1)
    async def connect_settings(self):
        await self.bot.wait_until_ready()
        self.bot.SettingsManager = SettingsManager(self.bot.db)
        await self.bot.SettingsManager.initialize()
        log.info("SettingsManager has been initialized.")

    @commands.group(aliases=["config", "settings"], invoke_without_command=True)
    async def set(self, ctx):
        prefix = await self.bot.SettingsManager.fetch_prefix(ctx.guild.id)
        embed = disnake.Embed(
            description=f"Use `{prefix}set`  to change settings!\n **__prefix__** : {prefix}"
        )
        embed.set_author(
            name=f"Settings for {ctx.guild.name}", icon_url=ctx.guild.icon.url
        )
        await ctx.send(embed=embed)

    @set.command(aliases=["p"])
    @is_guild_owner()
    async def prefix(self, ctx, prefix: str):
        if len(prefix) > 2:
            await ctx.send_line("The given prefix is too long try something smaller")
            return
        OGprefix = await self.bot.SettingsManager.fetch_prefix(ctx.guild.id)
        await self.bot.SettingsManager.set(ctx.guild.id, "prefix", prefix)
        self.bot.prefix_cache.delete_entry(ctx.guild.id)
        self.bot.prefix_cache.add_entry(
            ctx.guild.id, prefix, ttl=timedelta(hours=1), override=True
        )
        await ctx.send_line(
            f"prefix was changed from ***{OGprefix}*** - - > ***{prefix}***"
        )


def setup(bot):
    bot.add_cog(Settings(bot))
