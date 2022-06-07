from bot.db import MongoManager
from copy import deepcopy
from pprint import pprint
from bot.exceptions import ReactionExists, ReactionDoesNotExists


class ReactionRolesManager:
    def __init__(self, db: MongoManager):
        self.db = db
        self.cached = False

    async def initialize(self) -> None:
        self.reaction_roles = dict()
        r_roles = await self.db.reaction_roles.get_all()
        for guild in r_roles:
            self.reaction_roles[guild["_id"]] = guild
        self.cached = True

    async def fetch_guild_roles(self, guild_id: int):
        if self.cached:
            if guild_id in self.reaction_roles:
                data = deepcopy(self.reaction_roles[guild_id])
            else:
                data = None
        else:
            data = await self.db.reaction_roles.find({"_id": guild_id})

        return data

    async def add_reaction(
        self,
        guild_id: int = None,
        msg_id: str = None,
        role_id: int = None,
        emoji: str = None,
    ):
        data = {"emoji": str(emoji), "role_id": int(role_id)}

        guild_data = await self.fetch_guild_roles(guild_id)

        if not guild_data:

            guild_data = {
                "_id": guild_id,
                "roles": {
                    str(msg_id): [data],
                },
                "is_enabled": True,
            }

        else:
            if msg_id in guild_data["roles"]:
                if any(d == data for d in guild_data["roles"][msg_id]):
                    raise ReactionExists
                guild_data["roles"][msg_id].append(data)

            if msg_id not in guild_data["roles"]:
                guild_data["roles"][msg_id] = [data]

        if self.cached:
            self.reaction_roles[guild_id] = guild_data

        await self.db.reaction_roles.upsert(guild_data)

    async def remove_reaction(
        self, guild_id: int = None, msg_id: int = None, role_id: int = None
    ):
        guild_data = await self.fetch_guild_roles(guild_id)

        try:
            msg_list = guild_data["roles"][msg_id]
        except KeyError:
            raise ReactionDoesNotExists

        remove = next(d for d in msg_list if d["role_id"] == role_id)

        i = msg_list.index(remove)

        msg_list.pop(i)

        if self.cached:
            self.reaction_roles[guild_id] = guild_data

        await self.db.reaction_roles.upsert(guild_data)

    async def clear_reactions(self, guild_id: int = None, msg_id: str = None):
        guild_data = await self.fetch_guild_roles(guild_id)
        try:
            guild_data["roles"][msg_id] = []
        except KeyError:
            raise ReactionDoesNotExists

        if self.cached:
            self.reaction_roles[guild_id] = guild_data

        await self.db.reaction_roles.upsert(guild_data)

    async def rr_toggle(self, guild_id, value=None):

        guild_roles = await self.fetch_guild_roles(guild_id)

        if not value:
            if guild_roles["is_enabled"]:
                guild_roles["is_enabled"] = False
            else:
                guild_roles["is_enabled"] = True
        else:
            guild_roles["is_enabled"] = value

        if self.cached:
            self.reaction_roles[guild_id] = guild_roles

        await self.db.reaction_roles.upsert(guild_roles)

        return guild_roles["is_enabled"]
