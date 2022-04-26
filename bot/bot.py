import disnake
from disnake.ext import commands
import datetime
from datetime import timedelta
import humanize
from typing import (
    Optional,
    List,
)
from bot.context import CustomContext
from bot.exceptions import PrefixNotFound
from bot.cache import TimedCache
from bot.help import MyHelp
import logging

FMT = "[{levelname: ^7}] {name} : {message}"

FORMATS = {
    logging.DEBUG : FMT,
    logging.INFO  : f"\33[36m{FMT}\33[0m",
    logging.WARNING : f"\33[33m{FMT}\33[0m",
    logging.ERROR : f"\33[31m{FMT}\33[0m",
    logging.CRITICAL : f"\33[1m\33[31m{FMT}\33[0m"
}

class customformatter(logging.Formatter):
    def format(self, record):
        log_fmt = FORMATS[record.levelno]
        formatter = logging.Formatter(log_fmt, style="{")
        return formatter.format(record)

handler = logging.StreamHandler()
handler.setFormatter(customformatter())
logging.basicConfig(
    level = logging.INFO,
    handlers = [handler]
    )

gateway_logger = logging.getLogger("disnake.gateway")
gateway_logger.setLevel(logging.WARNING)
client_logger = logging.getLogger("disnake.client")
client_logger.setLevel(logging.WARNING)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        self._uptime = datetime.datetime.now()
        self.prefix_cache : TimedCache = TimedCache()
        self.DEFAULT_PREFIX : str = kwargs.pop("command_prefix")
        kwargs["command_prefix"] = self.get_command_prefix
        kwargs['help_command'] = MyHelp()
        self.logger = logging.getLogger(__name__)
        super().__init__(*args, **kwargs)


    @property
    def uptime(self) -> datetime.datetime:
        return self._uptime

    def get_bot_uptime(self) -> str:
        return humanize.precisedelta(self.uptime - datetime.datetime.now())

    async def get_context(self, message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):
        self.logger.info("\n\33[33m»»———-　starting bot　———-««\33[0m \n")
        self.load_extension("jishaku")

    async def on_message(self, msg):
        if msg.author.id == self.user.id:
            return
        await self.process_commands(msg)

    async def get_command_prefix(self, bot, message: disnake.Message) -> List[str]:
        try:
            prefix = await self.get_guild_prefix(guild_id=message.guild.id)

            prefix = self.get_case_insensitive_prefix(message.content, prefix)

            return commands.when_mentioned_or(prefix)(self, message)

        except (AttributeError, PrefixNotFound):
            prefix = self.get_case_insensitive_prefix(
                message.content, self.DEFAULT_PREFIX
            )
            return commands.when_mentioned_or(prefix)(self, message)

    @staticmethod
    def get_case_insensitive_prefix(content, prefix):
        if content.casefold().startswith(prefix.casefold()):
            # The prefix matches, now return the one the user used
            # such that dpy will dispatch the given command
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

        prefix_data = None

        if not prefix_data:
            raise PrefixNotFound

        prefix: Optional[str] = prefix_data.get("prefix")

        if not prefix:
            raise PrefixNotFound
        self.prefix_cache.add_entry(guild_id, prefix,ttl = timedelta(hours=1), override=True)
        return prefix


