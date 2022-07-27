from typing import Optional, Union
from copy import deepcopy

from bot.exceptions import InvalidSetting
from bot.db import MongoManager

sample = {
    "_id": "guildID",
    "prefix": ">",
}


class SettingsManager:
    """
    The manager for guild settings.

    Parameters
    ----------
    db : MongoManager
        The database to be used
    """

    def __init__(self, db: MongoManager) -> None:
        self.db = db
        self.cached = False
        self.types = ("prefix",)

    async def initialize(self) -> None:
        """
        Initializes/caches the database for settings!
        """
        self.cached = True
        self.settings = dict()
        settings = await self.db.settings.get_all()

        for guild in settings:
            self.settings[guild["_id"]] = guild

    async def fetch_settings(self, guild_id: int) -> dict:

        """
        Fetch guild settings

        Parameters
        ----------
        guild_id : int
            ID of the guild.

        Returns
        -------
        data : dict
            The settings of the guild.
            data = {
                "_id": "guildID",
                "prefix": "?",
                }
        """

        if not self.cached:
            data = await self.db.settings.find({"_id": guild_id})
        else:
            data = (
                deepcopy(self.settings[guild_id]) if guild_id in self.settings else None
            )

        if not data:
            data = {
                "_id": guild_id,
                "prefix": "?",
            }

        return data

    async def set(
        self, guild_id: int, _type: str, value: Union[str, int, bool]
    ) -> None:

        """
        Change a setting for a guild

        Parameters
        ----------
        guild_id : int
            ID of the guild  to change settings for.
        _type : str
            The setting to change.
        value : Optional[str, int, bool]
            The value of the setting

        Raises
        ------
        InvalidSetting
            Wrong type of setting to set
        """

        if _type not in self.types:
            raise InvalidSetting

        data = await self.fetch_settings(guild_id)
        data[_type] = value

        if self.cached:
            self.settings[guild_id] = data

        await self.db.settings.upsert(data)

    async def fetch_prefix(self, guild_id: int) -> str:
        """
        Fetch the prefix of a guild!

        Parameters
        ----------
        guild_id : int
            ID of the guild

        Returns
        -------
        prefix : str
            Prefix of the aforementioned guild

        """
        data = await self.fetch_settings(guild_id)
        return data["prefix"]
