from copy import deepcopy
from functools import wraps
from typing import Union, List

from bot.exceptions import ReactionExists, ReactionDoesNotExists
from bot.db import MongoManager

# sample = {
#     "_id" : "msgID"
#     "guild_id" : "guildID",
#     "roles" : [
#     {"emoji": str(emoji), "role_id": int(role_id)},
#     {"emoji": str(emoji), "role_id": int(role_id)},
#         ]
#     "is_enabled?" : True

# }


class ReactionRolesManager:
    """
    The manager used for reaction roles.

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
            data = await self.fetch_msg_roles(kwargs["guild_id"], kwargs["msg_id"])
            if len(data["roles"]) == 0:
                raise ReactionDoesNotExists
            else:
                return await fn(self, *args, **kwargs)

        return wrapper

    async def initialize(
        self,
    ) -> None:
        """
        Initializes/caches the database for reaction roles!

        """
        self.cached = True
        self.reaction_roles = dict()
        msgs = await self.db.reaction_roles.get_all()

        for msg in msgs:
            self.reaction_roles[msg["_id"]] = msg

    async def fetch_msg_roles(
        self,
        guild_id: int,
        msg_id: int,
    ) -> dict:
        """
        Fetch the reaction roles for a msg.

        Parameters
        ----------
        guild_id : int
            ID of the guild.
        msg_id : int
            ID of the msg.

        Returns
        -------

        data : dict
            The reactions roles bound to a msg.
            data = {
                "_id" : msg_id,
                "guild_id" : guild_id
                "roles" : [
                {"role_id" : 124, "emoji" : "hi"}, . . .
                ]
            }

        """

        if not self.cached:
            data = await self.db.reaction_roles.find({"_id": msg_id})
        else:
            data = (
                deepcopy(self.reaction_roles[msg_id])
                if msg_id in self.reaction_roles
                else None
            )

        if not data:
            data = {
                "_id": msg_id,
                "guild_id": guild_id,
                "roles": [],
                "is_enabled": True,
                "dm_info": {
                    "toggle": False,
                    "on_remove": "{role} was removed!",
                    "on_add": "{role} was added!",
                },
            }

        return data

    async def add_reaction(
        self,
        guild_id: int = None,
        msg_id: int = None,
        ch_id: int = None,
        role_id: int = None,
        emoji: str = None,
    ) -> None:
        """
        Add a reaction role to a msg.

        Parameters
        ----------
        guild_id : int
            ID of the guild.
        msg_id : int
            ID of the msg.
        role_id : int
            ID of the role to add.
        emoji : str
            The emote used for the above role.

        Raises
        ------
        ReactionExists
            The reaction already exists.

        """
        data = {"emoji": str(emoji), "role_id": int(role_id)}

        msg_data = await self.fetch_msg_roles(guild_id, msg_id)

        if any(d == data for d in msg_data["roles"]):
            raise ReactionExists

        msg_data["roles"].append(data)
        msg_data["channel_id"] = ch_id

        if self.cached:
            self.reaction_roles[msg_id] = msg_data

        await self.db.reaction_roles.upsert(msg_data)

    @database_check
    async def remove_reaction(
        self, guild_id: int = None, msg_id: int = None, role_id: int = None
    ) -> Union[str, int]:

        """
        Remove a reaction role to a msg.

        Parameters
        ----------
        guild_id : int
            ID of the guild.
        msg_id : int
            ID of the msg.
        role_id : int
            ID of the role to remove.
        Returns
        -------

        Union[str, int]

        channel_id : int
            The ID of the channel the msg is in .
             (for my convenience really)
        emoji : str
            The emote that was removed.
        Raises
        ------
        ReactionDoesNotExist
            The reaction does not exist.

        """

        msg_data = await self.fetch_msg_roles(guild_id, msg_id)

        roles_list = msg_data["roles"]

        remove = next(d for d in roles_list if d["role_id"] == role_id)

        i = msg_data["roles"].index(remove)

        msg_data["roles"].pop(i)

        if len(msg_data["roles"]) == 0:

            if self.cached:
                self.reaction_roles.pop(msg_id)

            await self.db.reaction_roles.delete(msg_data)
            return msg_data["channel_id"], remove["emoji"]

        if self.cached:
            self.reaction_roles[msg_id] = msg_data

        await self.db.reaction_roles.upsert(msg_data)
        return msg_data["channel_id"], remove["emoji"]

    @database_check
    async def clear_reactions(self, guild_id: int = None, msg_id: int = None) -> int:
        """
        Clear all reactions bound to a msg.

        Parameters
        ----------
        guild_id : int
            ID of the guild.
        msg_id : int
            ID of the msg.

        Returns
        -------
         channel_id : int
            The ID of the channel the msg is in .
             (for my convenience really)

        Raises
        ------
        ReactionDoesNotExist
            The given msg ID does not have reactions on it.
        """
        msg_data = await self.fetch_msg_roles(guild_id, msg_id)

        if self.cached:
            self.reaction_roles.pop(msg_id)

        await self.db.reaction_roles.delete(msg_data)
        return msg_data["channel_id"]

    @database_check
    async def toggle_roles(
        self, guild_id: int = None, msg_id: int = None, value: bool = None
    ) -> bool:
        """
        Toggles the reactions on/off.

        Parameters
        ----------
        guild_id : int
            ID of the guild.
        msg_id : int
            ID of the msg.
        value : bool
            Toggle whether true or false

        Raises
        ------
        ReactionDoesNotExist
            The given msg ID does not have reactions on it.
        """
        msg_data = await self.fetch_msg_roles(guild_id, msg_id)

        if not value:
            value = True if msg_data["is_enabled"] == False else False

        msg_data["is_enabled"] = value

        if self.cached:
            self.reaction_roles[msg_id] = msg_data

        await self.db.reaction_roles.upsert(msg_data)

        return value

    @database_check
    async def toggle_dm(
        self, guild_id: int = None, msg_id: int = None, value: bool = None
    ) -> bool:
        """
        Toggle whether the bot should send a msg when a user adds a role.

        Parameters
        ----------
        guild_id : int
            ID of the guild.
        msg_id : int
            ID of the msg.
        value : bool
            Whether to send a DM or not.
        Raises
        ------
        ReactionDoesNotExist
            The given msg ID does not have reactions on it.
        """

        msg_data = await self.fetch_msg_roles(guild_id, msg_id)

        dm_data = msg_data["dm_info"]

        if not value:
            value = True if dm_data["toggle"] == False else False

        dm_data["toggle"] = value

        if self.cached:
            self.reaction_roles[msg_id] = msg_data

        await self.db.reaction_roles.upsert(msg_data)
        return value

    @database_check
    async def set_dm_msg(
        self,
        guild_id: int = None,
        msg_id: int = None,
        on_remove: bool = False,
        on_add: bool = False,
        msg: str = None,
    ) -> None:
        """
        Add the msg to send when a user reacts.

        Parameters
        ----------
        guild_id : int
            ID of the guild.
        msg_id : int
            ID of the msg.
        msg : str
            The msg to send

        Raises
        ------
        ReactionDoesNotExist
            The given msg ID does not have reactions on it.
        """
        msg_data = self.fetch_msg_roles(guild_id, msg_id)
        data = msg_data["dm_info"]

        if on_add:
            data["on_add"] = msg
        if on_remove:
            data["on_remove"] = msg

        if self.cached:
            self.reaction_roles[msg_id] = msg_data

        await self.db.reaction_roles.upsert(msg_data)

    async def reaction_add(self, payload):
        """
        Event for "on_raw_reaction_add"

        """
        if payload.user_id == self.bot.user.id:
            return

        data = await self.fetch_msg_roles(payload.guild_id, payload.message_id)

        if len(data["roles"]) == 0:
            return

        if not data["is_enabled"]:
            return

        guild = await self.bot.fetch_guild(payload.guild_id)

        emote_data = next(d for d in data["roles"] if d["emoji"] in str(payload.emoji))

        role = guild.get_role(emote_data["role_id"])

        user = await guild.fetch_member(payload.user_id)

        if role not in user.roles:
            await user.add_roles(role, reason="Reaction roles")

            if not data["dm_info"]["toggle"]:
                return

            send = data["dm_info"]["on_add"]
            await user.send(f"*__{guild.name}__* : {send.format(role=role)}")

    async def reaction_remove(self, payload):
        """
        Event for "on_raw_reaction_remove"

        """
        if payload.user_id == self.bot.user.id:
            return

        data = await self.fetch_msg_roles(payload.guild_id, payload.message_id)

        if len(data["roles"]) == 0:
            return

        if not data["is_enabled"]:
            return

        guild = await self.bot.fetch_guild(payload.guild_id)

        emote_data = next(d for d in data["roles"] if d["emoji"] in str(payload.emoji))

        role = guild.get_role(emote_data["role_id"])

        user = await guild.fetch_member(payload.user_id)

        if role in user.roles:
            await user.remove_roles(role, reason="Reaction roles")

            if not data["dm_info"]["toggle"]:
                return

            send = data["dm_info"]["on_remove"]
            await user.send(f"*__{guild.name}__* : {send.format(role=role)}")
