from pprint import pprint

import discord
from discord.ext import commands, tasks

from bot.db.managers import ReactionRolesManager


class ReactionRoles(commands.Cog):
    """Contains all the cmds related to reaction roles"""

    def __init__(self, bot):
        self.bot = bot
        self.cache_roles.start()

    def can_manage_roles():
        async def predicate(ctx):
            return (
                ctx.guild.owner_id == ctx.author.id
                or ctx.author.guild_permissions.administrator
                or ctx.author.guild_permissions.manage_roles
            )

        return commands.check(predicate)

    @tasks.loop(count=1)
    async def cache_roles(self) -> None:
        """
        Caching roles as well,what else?
        """
        await self.bot.wait_until_ready()
        self.ReactionRolesManager = ReactionRolesManager(self.bot.db, self.bot)
        await self.ReactionRolesManager.initialize()
        self.bot.add_listener(
            self.ReactionRolesManager.reaction_add, "on_raw_reaction_add"
        )
        self.bot.add_listener(
            self.ReactionRolesManager.reaction_remove, "on_raw_reaction_remove"
        )

    @commands.group(name="rroles", aliases=["rr"], invoke_without_command=True)
    @can_manage_roles()
    async def reaction_roles(self, ctx):
        """
        Base cmd for reactionroles
        """

    @reaction_roles.command()
    @can_manage_roles()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def add(self, ctx, channel: discord.TextChannel, msg: int):
        """
        Add reaction roles to a msg
        """
        # Input validation
        if msg <= 0:
            await ctx.send_line("Invalid message ID.")
            return

        try:
            message = await channel.fetch_message(int(msg))
        except discord.NotFound:
            await ctx.send_line("Message not found.")
            return

        while True:
            emoji = await ctx.get_input("What emoji you want to use?")
            # Basic emoji validation
            if not emoji or len(emoji.strip()) == 0:
                await ctx.send_line("Emoji cannot be empty.")
                continue
            if len(emoji) > 100:  # Arbitrary limit
                await ctx.send_line("Emoji too long.")
                continue

            role_input = await ctx.get_input(
                f"Type the name of the role you want to bind to {emoji}."
            )
            if not role_input or len(role_input.strip()) == 0:
                await ctx.send_line("Role cannot be empty.")
                continue

            if role_input.isdigit():
                role = discord.utils.get(ctx.guild.roles, id=int(role_input))
            elif role_input.startswith("<@&"):
                role_id = role_input.replace("<@&", "").replace(">", "")
                if not role_id.isdigit():
                    await ctx.send_line("Invalid role mention.")
                    continue
                role = discord.utils.get(ctx.guild.roles, id=int(role_id))
            else:
                role = discord.utils.get(ctx.guild.roles, name=str(role_input))

            if not role:
                await ctx.send_line("Role not found.")
                continue

            # Check if bot can manage the role
            if role >= ctx.guild.me.top_role:
                await ctx.send_line("I cannot manage this role (it's above my highest role).")
                continue

            await self.ReactionRolesManager.add_reaction(
                guild_id=ctx.guild.id,
                msg_id=msg,
                ch_id=channel.id,
                role_id=role.id,
                emoji=emoji,
            )
            await ctx.send_line("It was added!")

            try:
                await message.add_reaction(str(emoji))
            except discord.HTTPException:
                await ctx.send_line("Failed to add reaction to message.")

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
    @can_manage_roles()
    async def remove(self, ctx, msg_id: int):
        """
        Remove reactions bound to a role.
        """
        while True:

            role = await ctx.get_input(f"Type the name of the role you want to remove.")

            if role.isdigit():
                role = discord.utils.get(ctx.guild.roles, id=int(role))

            elif role.startswith("<@&"):
                role = role.replace("<@&", "").replace(">", "")
                role = discord.utils.get(ctx.guild.roles, id=int(role))

            else:
                role = discord.utils.get(ctx.guild.roles, name=str(role))

            ch, emote = await self.ReactionRolesManager.remove_reaction(
                guild_id=ctx.guild.id,
                msg_id=msg_id,
                role_id=role.id,
            )

            channel = ctx.guild.get_channel(ch)

            message = await channel.fetch_message(msg_id)

            await message.clear_reaction(emote)
            await ctx.send_line(f"{role.mention} was removed from ReactionRoles.")

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
    @can_manage_roles()
    async def clear(self, ctx, msg_id: int):
        """
        Clear all the reactions bound to a msg
        """
        ch = await self.ReactionRolesManager.clear_reactions(
            guild_id=ctx.guild.id,
            msg_id=msg_id,
        )
        await ctx.send_line("All roles were removed from ReactionRoles.")
        channel = ctx.guild.get_channel(ch)
        message = await channel.fetch_message(msg_id)
        await message.clear_reactions()

    @reaction_roles.group(invoke_without_command=True)
    async def toggle(self, ctx):
        """
        Toggle whether roles/DMs should be on or not.
        """
        pass

    @toggle.command()
    @can_manage_roles()
    async def roles(self, ctx, msg_id: int, value: bool = None):
        """
        Toggle reactions roles on/off
        """
        val = await self.ReactionRolesManager.toggle_roles(
            guild_id=ctx.guild.id, msg_id=msg_id, value=value if value else None
        )
        if val:
            val = "on"
        else:
            val = "off"
        await ctx.send_line(f"The roles toggle was turned {val}!")

    @toggle.command()
    @can_manage_roles()
    async def dm(self, ctx, msg_id: int, value: bool = None):
        """
        Toggle whether a bot should send a DM on reaction or not
        """
        val = await self.ReactionRolesManager.toggle_dm(
            guild_id=ctx.guild.id, msg_id=msg_id, value=value if value else None
        )
        if val:
            val = "on"
        else:
            val = "off"
        await ctx.send_line(f"The DM toggle was turned {val}!")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send_line(f"You're on cooldown. Try again in {error.retry_after:.1f} seconds.")
        else:
            # Re-raise for other handlers
            raise error


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
