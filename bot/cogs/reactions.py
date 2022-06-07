from disnake.ext import commands, tasks
import asyncio
from bot.db import ReactionRolesManager
import logging
import disnake
from pprint import pprint
from datetime import timedelta

log = logging.getLogger(__name__)


class ReactionRoles(commands.Cog):
    """Contains all the cmds related to reaction roles"""

    def __init__(self, bot):
        self.bot = bot
        self.connect_roles.start()

    @tasks.loop(count=1)
    async def connect_roles(self):
        await self.bot.wait_until_ready()
        self.ReactionRolesManager = ReactionRolesManager(self.bot.db)
        await self.ReactionRolesManager.initialize()
        log.info("ReactionRolesManager has been initialized.")

    @commands.group(name="rroles", aliases=["rr"], invoke_without_command=True)
    async def reaction_roles(self, ctx):
        return

    @reaction_roles.command()
    async def add(self, ctx, channel: disnake.TextChannel, msg):
        while True:
            message = await channel.fetch_message(int(msg))

            emoji = await ctx.get_input("Type the emoji you want to use")

            role = await ctx.get_input(
                f"Type the name of the role you want to bind to emoji"
            )

            if role.isdigit():
                role = disnake.utils.get(ctx.guild.roles, id=int(role))

            elif role.startswith("<@&"):
                role = role.replace("<@&", "").replace(">", "")
                role = disnake.utils.get(ctx.guild.roles, id=int(role))

            else:
                role = disnake.utils.get(ctx.guild.roles, name=str(role))

            await self.ReactionRolesManager.add_reaction(
                guild_id=ctx.guild.id, msg_id=msg, role_id=role.id, emoji=emoji
            )
            await ctx.send_line("It was added!")

            await message.add_reaction(str(emoji))

            val = await ctx.confirm(
                "Would you like to continue adding roles to the same message?",
                delete_after=True,
            )
            if val:
                continue
            else:
                await ctx.send_line("Gotcha")
                break

    @reaction_roles.command()
    async def remove(self, ctx, role: disnake.Role, msg_id: str):
        await self.ReactionRolesManager.remove_reaction(
            guild_id=ctx.guild.id,
            msg_id=str(msg_id),
            role_id=role.id,
        )
        await ctx.send_line(f"{role} was remove from ReactionRoles.")

    @reaction_roles.command()
    async def clear(self, ctx, channel: disnake.TextChannel, msg_id: str):
        await self.ReactionRolesManager.clear_reactions(
            guild_id=ctx.guild.id,
            msg_id=msg_id,
        )
        await ctx.send_line("All roles were removed from ReactionRoles.")
        message = await channel.fetch_message(msg_id)
        await message.clear_reactions()

    @reaction_roles.command()
    async def toggle(self, ctx, msg_id, value: bool = None):
        val = await self.ReactionRolesManager.rr_toggle(
            ctx.guild.id, value=value if value else None
        )
        if val:
            val = "on"
        else:
            val = "off"
        await ctx.send_line(f"The roles were toggled {val}!")

    @commands.Cog.listener("on_raw_reaction_add")
    async def reaction_add(self, payload):

        if payload.user_id == self.bot.user.id:
            return

        data = await self.ReactionRolesManager.fetch_guild_roles(payload.guild_id)

        if not data or not data["is_enabled"]:
            return

        guild_reaction_roles = data["roles"]

        if str(payload.message_id) not in guild_reaction_roles:
            return

        guild = await self.bot.fetch_guild(payload.guild_id)

        emoji_name = str(payload.emoji)

        msg_roles = guild_reaction_roles[str(payload.message_id)]

        roles_data = next(x for x in msg_roles if x["emoji"] in emoji_name)

        role = guild.get_role(roles_data["role_id"])

        member = await guild.fetch_member(payload.user_id)

        if role not in member.roles:
            await member.add_roles(role, reason="Reaction role.")

    @commands.Cog.listener("on_raw_reaction_remove")
    async def reaction_remove(self, payload):

        if payload.user_id == self.bot.user.id:
            return

        data = await self.ReactionRolesManager.fetch_guild_roles(payload.guild_id)

        if not data or not data["is_enabled"]:
            return

        guild_reaction_roles = data["roles"]

        if str(payload.message_id) not in guild_reaction_roles:
            return

        guild = await self.bot.fetch_guild(payload.guild_id)

        emoji_name = str(payload.emoji)

        msg_roles = guild_reaction_roles[str(payload.message_id)]

        roles_data = next(x for x in msg_roles if x["emoji"] in emoji_name)

        role = guild.get_role(roles_data["role_id"])

        member = await guild.fetch_member(payload.user_id)

        if role in member.roles:
            await member.remove_roles(role, reason="Reaction role.")


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
