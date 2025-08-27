from copy import deepcopy
from functools import wraps
from typing import Optional, Union, List

import discord
from discord.ext import commands

from bot.exceptions import EmbedExists, EmbedDoesNotExist
from bot.db import MongoManager


sample = {
    "_id": 1243,
    "embeds": [{"name": "hi", "created_by": "jioy", "embed": {"data": 1}}],
}


class EmbedManager:

    """
    The manager used for embeds.

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
            data = await self.fetch_guild_embeds(kwargs["guild_id"])
            if len(data["embeds"]) == 0:
                raise EmbedDoesNotExist
            else:
                return await fn(self, *args, **kwargs)

        return wrapper

    async def initialize(self) -> None:
        """
        Initializes/caches the database for ARs!

        """
        self.cached = True
        self.embeds = dict()

        embeds = await self.db.embeds.get_all()

        for embed in embeds:
            self.embeds[embed["_id"]] = embed

    async def fetch_guild_embeds(
        self, guild_id: int, embed: Optional[str, int] = None
    ) -> dict:
        """
        Fetch all the autoresponders for a guild.

        Parameters
        ----------
        guild_id : int
            ID of the guild you want to fetch ARs for.
        embed: Optional[str]
            The name of the embed to look for in said guild embeds.

        Returns
        -------
        data : dict
            The data from the db.
        """

        if not self.cached:
            guild_data = await self.db.embeds.find({"_id": guild_id})
        else:
            guild_data = deepcopy(self.embeds[guild_id])

        if not guild_data:
            guild_data = {"_id": guild_id, "embeds": []}

        if not embed:
            return guild_data

        try:
            if isinstance(embed, str):
                embed_data = next(x for x in guild_data["embeds"] if x["name"] == embed)
                return embed_data

            if isinstance(embed, int):
                embed_data = guild_data["embeds"][trigger]
                return embed_data

        except StopIteration, IndexError:
            raise EmbedDoesNotExist

    async def add_embed(
        self,
        guild_id: int = None,
        user_id: int = None,
        embed_name: str = None,
        embed_data: dict = None,
    ) -> None:
        """
        Add embeds to a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.
        user_id : int
            The ID of the user creating the AR
        embed_name : str
            The name for the embed
        embed_data : dict
            The json data for the embed

        Raises
        ------
        TriggerExists
            The trigger already exists.
        """

        data = {
            "name" : embed_name,
            "created_by" : user_id,
            "embed" : embed_data.
        }
