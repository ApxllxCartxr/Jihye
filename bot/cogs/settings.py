import disnake
from disnake.ext import commands, tasks
from datetime import timedelta

from bot.db.managers import SettingsManager


class Settings(commands.Cog):
    """
    Contains all the cmds related to guild settings.
    """

    def __init__(self, bot):
        self.bot = bot
        self.cache_settings.start()

    def is_guild_owner():
        async def predicate(ctx):
            return (
                ctx.guild.owner_id == ctx.author.id
                or ctx.author.guild_permissions.administrator
            )

        return commands.check(predicate)

    @tasks.loop(count=1)
    async def cache_settings(self) -> None:
        """
        Caching settings,what else is there to say?
        """
        await self.bot.wait_until_ready()
        self.bot.SettingsManager = SettingsManager(self.bot.db)
        await self.bot.SettingsManager.initialize()

    @commands.group(aliases=["config", "settings"], invoke_without_command=True)
    async def set(self, ctx):
        """
        Display the current settings for your guild
        """
        prefix = await self.bot.SettingsManager.fetch_prefix(ctx.guild.id)
        embed = disnake.Embed(
            description=f"Use `{prefix}set`  to change settings!\n **__prefix__** : {prefix}"
        )
        embed.set_author(
            name=f"Settings for {ctx.guild.name}", icon_url=ctx.guild.icon.url
        )
        await ctx.send(embed=embed)

    @set.command(aliases=["p", "pre"])
    @is_guild_owner()
    async def prefix(self, ctx, prefix: str):
        """
        Use to change the guild prefix
        """
        if len(prefix) > 2:
            await ctx.send_line("The given prefix is too long,try something smaller")
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
