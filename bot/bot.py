import os
import datetime
from datetime import timedelta
import humanize
from typing import List, Optional

import discord
from discord.ext import commands

from bot.exceptions import PrefixNotFound
from bot.context import CustomContext
from bot.help import MyHelp
from bot.db import MongoManager
from bot.db.managers import SettingsManager
from bot.cache import TimedCache


class BaseBot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:

        self.__uptime = datetime.datetime.now()

        self.DEFAULT_PREFIX: str = kwargs.pop("command_prefix")
        self.prefix_cache: TimedCache = TimedCache()
        kwargs["command_prefix"] = self.get_command_prefix

        self.db: MongoManager = MongoManager(
            kwargs.pop("mongo_url"), kwargs.pop("db_name", None)
        )
        kwargs["help_command"] = MyHelp()

        super().__init__(*args, **kwargs)

    @property
    def uptime(self) -> datetime.datetime:
        return self.__uptime

    def get_uptime(self) -> str:
        return humanize.precisedelta(self.uptime - datetime.datetime.now())

    async def get_context(self, msg, *, cls=CustomContext) -> CustomContext:
        return await super().get_context(msg, cls=cls)

    async def on_ready(self) -> None:
        await self.load_extension("jishaku")

        for filename in os.listdir("bot/cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"bot.cogs.{filename[:-3]}")
                print(f"❜ ─ {filename[:-3]} was loaded . ─ ❛")

    async def on_message(self, msg: discord.Message) -> None:
        if msg.author.id == self.user.id:
            return
        await self.process_commands(msg)

    async def get_command_prefix(self, bot, msg: discord.Message) -> List[str]:
        """
        Returns a list of prefixes for a guild

        Parameters
        ----------
        bot : commands.Bot/BaseBot
            The bot instance

        msg : discord.Message
            The msg object

        Returns
        -------
        List[str]
            A list of prefixes
            i.e bot_mention, "?" etc.
        """

        try:
            prefix = await self.get_guild_prefix(guild_id=msg.guild.id)
            prefix = self.get_case_insensitive_prefix(msg.content, prefix)

        except (AttributeError, PrefixNotFound):
            prefix = self.get_case_insensitive_prefix(msg.content, self.DEFAULT_PREFIX)

        return commands.when_mentioned_or(prefix)(self, msg)

    @staticmethod
    def get_case_insensitive_prefix(content, prefix) -> str:
        """
        Returns a case insensitive prefix....obviously,

        Parameters
        ----------
        content : str
            The content of the msg

        prefix : str
            The prefix returned from self.get_guild_prefix

        Returns
        -------
            str
                The prefix

        """
        if content.casefold().startswith(prefix.casefold()):
            prefix_length = len(prefix)
            prefix = content[:prefix_length]
        return prefix

    async def get_guild_prefix(self, guild_id: Optional[int] = None) -> str:
        """
        Using a cached property fetch prefixes
        for a guild and return em.
        Parameters
        ----------
        guild_id : int
            The guild we want prefixes for
        Returns
        -------
        str
            The prefix
        Raises
        ------
        PrefixNotFound
            We failed to find and
            return a valid prefix
        """

        if guild_id in self.prefix_cache:
            return self.prefix_cache.get_entry(guild_id)

        prefix = await self.SettingsManager.fetch_prefix(guild_id)

        if not prefix:
            raise PrefixNotFound

        if prefix != self.DEFAULT_PREFIX:
            self.prefix_cache.add_entry(
                guild_id, prefix, ttl=timedelta(minutes=30), override=True
            )
        return prefix
