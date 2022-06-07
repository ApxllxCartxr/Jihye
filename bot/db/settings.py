sample = {
    "_id": "guildiID",
    "prefix": ">",
    "modlogID": "id",
    "modlog_toggle": True,
}

from bot.db import MongoManager
from copy import deepcopy
from pprint import pprint
from bot.exceptions import InvalidSetting
from disnake.ext.commands import Paginator


class SettingsManager:
    def __init__(self, db: MongoManager):
        self.db = db
        self.cached = False
        self.types = (
            "prefix",
            "modlogID",
            "modlog_toggle",
        )

    async def initialize(self) -> None:
        self.settings = dict()
        settings = await self.db.settings.get_all()
        for user in settings:
            self.settings[user["_id"]] = user
        self.cached = True

    async def fetch_prefix(self, guild_id) -> str:
        if self.cached:
            prefix = (
                self.settings[guild_id]["prefix"] if guild_id in self.settings else None
            )
        else:
            data = await self.db.settings.find({"_id": guild_id})
            prefix = data["prefix"] if data else None
        return prefix

    async def set(self, guild_id, SettingType, value):

        if SettingType not in self.types:
            raise InvalidSetting

        if self.cached:

            if guild_id in self.settings:
                settings = deepcopy(self.settings[guild_id])
                settings[SettingType] = value
                self.settings[guild_id] = settings

            else:
                settings = {
                    "_id": guild_id,
                    "prefix": "?",
                    "modlogID": None,
                    "modlog_toggle": False,
                }
                settings[SettingType] = value
                self.settings[guild_id] = settings

            await self.db.settings.upsert(settings)
            return

        else:
            data = await self.db.settings.find({"_id": guild_id})

            if not data:

                settings = {
                    "_id": guild_id,
                    "prefix": "?",
                    "modlogID": None,
                    "modlog_toggle": False,
                }
                settings[SettingType] = value

                await self.db.settings.upsert(settings)
                return
            if data:
                data[SettingType] = value
                await self.db.settings.upsert(data)
