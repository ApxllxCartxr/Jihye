from copy import deepcopy
from functools import wraps
from typing import Optional, Union, List, Tuple

import discord
from discord.ext import commands
import jinja2.sandbox

from bot.exceptions import TriggerExists, TriggerDoesNotExist
from bot.db import MongoManager

# sample = {
#     "_id" : "guildID",
#     "enabled" : True or False,
#     "autoresponders" : [
#         {"trigger" : "hi", "response" : "yes?", "is_embed?" : True,"created_by" : 12234}
#     ]
# }


class ARManager:

    """
    The manager used for autoresponders/triggers.

    Parameters
    ----------
    db : MongoManager
        The database to be used.
    bot : BaseBot
        The bot instance used to handle events.

    """

    def __init__(self, db: MongoManager, bot) -> None:
        self.db = db
        self.bot = bot
        self.cached = False

    def database_check(fn):
        @wraps(fn)
        async def wrapper(self, *args, **kwargs):
            data = await self.fetch_guild_ars(args[0])
            if len(data["autoresponders"]) == 0:
                raise TriggerDoesNotExist
            else:
                return await fn(self, *args, **kwargs)

        return wrapper

    async def initialize(self) -> None:
        """
        Initializes/caches the database for ARs!

        """
        self.cached = True
        self.ARs = dict()
        guilds = await self.db.autoresponders.get_all()

        for guild in guilds:
            self.ARs[guild["_id"]] = guild

    async def fetch_guild_ars(
        self, guild_id: int, trigger: Optional[Union[str, int]] = None
    ) -> dict:
        """
        Fetch all the autoresponders for a guild.

        Parameters
        ----------
        guild_id : int
            ID of the guild you want to fetch ARs for.
        trigger : Optional[str]
            The trigger to look for in said guild ARs

        Returns
        -------
        data : dict
            The data from the db.
        """

        if not self.cached:
            data = await self.db.autoresponders.find({"_id": guild_id})
        else:
            data = deepcopy(self.ARs[guild_id]) if guild_id in self.ARs else None

        if not data:
            data = {"_id": guild_id, "is_enabled?": True, "autoresponders": []}

        if not trigger:
            return data

        try:
            if trigger.isdigit():
                trigger_data = data["autoresponders"][int(trigger) - 1]
                return trigger_data

            if isinstance(trigger, str):
                trigger_data = next(
                    x for x in data["autoresponders"] if x["trigger"] == trigger
                )
                return trigger_data

        except (StopIteration, IndexError):
            raise TriggerDoesNotExist

    async def add_ar(
        self,
        guild_id: int = None,
        user_id: int = None,
        trigger: str = None,
        response: Union[str, dict] = None,
    ) -> dict:
        """
        Add autoresponders to a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.
        user_id : int
            The ID of the user creating the AR
        trigger : str
            The trigger word for the AR
        response : Union[str, dict]
            The response for the AR

        Raises
        ------
        TriggerExists
            The trigger already exists.
        """

        data = {
            "trigger": trigger,
            "response": response,
            "created_by": user_id,
            "is_embed?": False,
            "reply?": False,
        }

        guild_data = await self.fetch_guild_ars(guild_id)

        if any(d["trigger"] == data["trigger"] for d in guild_data["autoresponders"]):
            raise TriggerExists

        if isinstance(response, dict):
            data["is_embed?"] = True

        guild_data["autoresponders"].append(data)

        if self.cached:
            self.ARs[guild_id] = guild_data

        await self.db.autoresponders.upsert(guild_data)

    @database_check
    async def remove_ar(
        self, guild_id: int = None, trigger: Union[str, int] = None
    ) -> None:
        """
        Remove autoresponders from a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.
        trigger : str/int
            The trigger word for the AR
        Raises
        ------
        TriggerDoesNotExist
            The trigger already exists.
        """

        guild_data = await self.fetch_guild_ars(guild_id)

        trigger_data = await self.fetch_guild_ars(guild_id, trigger)

        i = guild_data["autoresponders"].index(trigger_data)

        guild_data["autoresponders"].pop(i)

        if len(guild_data["autoresponders"]) == 0:
            if self.cached:
                self.ARs.pop(guild_id)
            await self.db.autoresponders.delete(guild_id)

        if self.cached:
            self.ARs[guild_id] = guild_data

        await self.db.autoresponders.upsert(guild_data)

    @database_check
    async def format_guild_ars(self, guild_id: int) -> List[str]:
        """
        Format all the ARs in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.

        Returns
        -------
        data : List[str]
            The formatted data.

        Raises
        ------
        TriggerDoesNotExist
            The guild does not have any ARs.
        """

        guild_data = await self.fetch_guild_ars(guild_id)

        paginator = commands.Paginator(prefix="", suffix="", linesep="\n")

        for i, ar in enumerate(guild_data["autoresponders"]):
            paginator.add_line(f"{i + 1}) {ar['trigger']}")

        return paginator.pages

    async def format_ar_data(
        self, guild_id: int, trigger: Union[str, int] = None
    ) -> Tuple[str, Optional[discord.Embed]]:
        """
        Get trigger data and format

        Parameters
        ----------
        guild_id : int
            The ID of the guild.
        trigger : str/int
            The trigger word for the AR

        Returns
        -------

        Raises
        ------
        TriggerDoesNotExist
            The trigger does not exist.
        """

        trigger_data = await self.fetch_guild_ars(guild_id, trigger)

        user = await self.bot.getch_user(trigger_data["created_by"])

        data = f"""**__trigger__** : {trigger_data["trigger"]}
                   **__embed?__** : {trigger_data["is_embed?"]}
                   **__created by__** : {user.mention}\n"""

        if not trigger_data["is_embed?"]:
            embed = f"**__resp.__** :\n ```{trigger_data['response']}```"
            data = data + embed
            return data, None

        embed = discord.Embed.from_dict(trigger_data["response"])
        data = data + "**__resp.__** : The response is an embed."
        return data, embed

    async def on_msg(self, msg):
        """
        Event to handle AR stuff.
        """
        ar_data = await self.fetch_guild_ars(msg.guild.id)

        if len(ar_data["autoresponders"]) == 0:
            return

        if not ar_data["is_enabled?"]:
            return

        if not any(d["trigger"] == msg.content for d in ar_data["autoresponders"]):
            return

        data = await self.fetch_guild_ars(msg.guild.id, trigger=msg.content)

        variables = {
            "guild_name": msg.guild.name,
            "guild_id": msg.guild.id,
            "user_mention": msg.author.mention,
            "user_name": msg.author.display_name,
            "guild_mc": sum(not member.bot for member in msg.guild.members),
            "guild_mc_ord": self.make_ordinal(
                sum(not member.bot for member in msg.guild.members)
            ),
            "timestamp": msg.created_at,
        }

        env = jinja2.sandbox.SandboxedEnvironment()

        if data["is_embed?"]:
            embed = discord.Embed.from_dict(data["response"])
            try:
                embed.title = env.from_string(embed.title).render(**variables)
            except (jinja2.TemplateError, TypeError):
                pass  # Keep original if templating fails
            try:
                embed.description = env.from_string(embed.description).render(**variables)
            except (jinja2.TemplateError, TypeError):
                pass
            try:
                if embed.footer:
                    embed.set_footer(text=env.from_string(embed.footer.text).render(**variables))
            except (jinja2.TemplateError, TypeError):
                pass
            try:
                if embed.author:
                    embed.set_author(name=env.from_string(embed.author.name).render(**variables))
            except (jinja2.TemplateError, TypeError):
                pass

            for field in embed.fields:
                try:
                    field["name"] = env.from_string(field["name"]).render(**variables)
                except (jinja2.TemplateError, TypeError):
                    pass
                try:
                    field["value"] = env.from_string(field["value"]).render(**variables)
                except (jinja2.TemplateError, TypeError):
                    pass

            await msg.channel.send(embed=embed)
            return

        try:
            msg_data = env.from_string(data["response"]).render(**variables)
        except (jinja2.TemplateError, TypeError):
            msg_data = data["response"]  # Fallback to original
        await msg.channel.send(msg_data)

    def make_ordinal(self, n):
        """
        Convert an integer into its ordinal representation::

            make_ordinal(0)   => '0th'
            make_ordinal(3)   => '3rd'
            make_ordinal(122) => '122nd'
            make_ordinal(213) => '213th'
        """
        n = int(n)
        if 11 <= (n % 100) <= 13:
            suffix = "th"
        else:
            suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
        return str(n) + suffix
