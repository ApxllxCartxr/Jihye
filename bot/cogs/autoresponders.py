from typing import Union, Optional
from pprint import pprint

import discord
from discord.ext import commands, tasks

from bot.exceptions import TriggerDoesNotExist, TriggerExists
from bot.paginators import SimplePaginator
from bot.db.managers import ARManager


class Autoresponders(commands.Cog):
    """Contains all the cmds related to autoresponders"""

    def __init__(self, bot):
        self.bot = bot
        self.cache_triggers.start()

    def can_manage_msgs():
        def predicate(ctx):
            return (
                ctx.guild and (
                    ctx.guild.owner_id == ctx.author.id
                    or ctx.author.guild_permissions.administrator
                    or ctx.author.guild_permissions.manage_messages
                )
            )

        return commands.check(predicate)

    def cog_unload(self):
        try:
            self.bot.remove_listener(self.ARManager.on_msg, "on_message")
        except Exception:
            pass

    @tasks.loop(count=1)
    async def cache_triggers(self):
        """
        Caching triggers as well,what else?
        """
        await self.bot.wait_until_ready()
        self.ARManager = ARManager(self.bot.db, self.bot)
        await self.ARManager.initialize()
        self.bot.add_listener(self.ARManager.on_msg, "on_message")

    @commands.command(aliases=["var"])
    async def variables(self, ctx):
        """
        Show the variables you can use for ARs
        """
        things = """{guild_name} : The name of the guild.
                    {guild_id} : The ID of the guild.
                    {user_mention} : The mention of the user who used the AR.
                    {user_name} : The display name of the user.
                    {guild_mc} : The member count of the guild.
                    {guild_mc_ord} : The ordinal version of the above thing.
                    {timestamp} : The timestamp on the msg (Today at 4:56pm etc.)
                    """
        await ctx.send_line(things)

    @commands.group(
        name="ar", aliases=["trigger", "autores"], invoke_without_command=True
    )
    @can_manage_msgs()
    async def ar(self, ctx, *, ar: Optional[Union[str, int]] = None):
        """
        Gives the list of ARs for the guild
        """
        if not ar:
            try:
                data = await self.ARManager.format_guild_ars(ctx.guild.id)
                embeds = []
                for page in data:
                    embed = discord.Embed(
                        title=f"{ctx.guild.name}'s ARs", description=page
                    )
                    embeds.append(embed)
                paginator = SimplePaginator(pages=embeds)
                await paginator.send(ctx)
            except TriggerDoesNotExist:
                await ctx.send_line("This server has no ARs.")

            return

        data, embed = await self.ARManager.format_ar_data(ctx.guild.id, ar)

        await ctx.send_line(data)

        if embed:
            await ctx.send(embed=embed)

    @ar.group(aliases=["+"], invoke_without_command=True)
    @can_manage_msgs()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def add(self, ctx, *, name: str):
        """
        Add an AR to your guild.
        """
        # Input validation
        if not name or len(name.strip()) == 0:
            await ctx.send_line("Trigger cannot be empty.")
            return
        if len(name) > 100:
            await ctx.send_line("Trigger is too long (max 100 characters).")
            return
        # Basic sanitization: remove potential injection chars, but allow common ones
        name = name.strip()

        val = await ctx.get_input("What should the response of the AR be?")
        if not val or len(val.strip()) == 0:
            await ctx.send_line("Response cannot be empty.")
            return
        if len(val) > 2000:  # Discord message limit
            await ctx.send_line("Response is too long (max 2000 characters).")
            return
        val = val.strip()

        try:
            await self.ARManager.add_ar(
                guild_id=ctx.guild.id, user_id=ctx.author.id, trigger=name, response=val
            )

            await ctx.send_line("The AR was added successfully!")

        except TriggerExists:
            await ctx.send_line("The AR already exists.")

    @add.command(aliases=["em"])
    @can_manage_msgs()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def embed(self, ctx, *, name: str):
        """
        Add an embed AR in your guild
        """
        # Input validation for trigger
        if not name or len(name.strip()) == 0:
            await ctx.send_line("Trigger cannot be empty.")
            return
        if len(name) > 100:
            await ctx.send_line("Trigger is too long (max 100 characters).")
            return
        name = name.strip()

        title = await ctx.get_input("What should the title of the embed be?")
        if len(title) > 256:  # Discord embed title limit
            await ctx.send_line("Title is too long (max 256 characters).")
            return

        embed = discord.Embed(title=title)

        desc = await ctx.get_input("What should be the desc. of the embed be?")
        if len(desc) > 4096:  # Discord embed desc limit
            await ctx.send_line("Description is too long (max 4096 characters).")
            return
        embed.description = desc

        color = await ctx.get_input(
            "What should the color of the embed be?(only accepts #fffff like values)"
        )
        conv = commands.ColorConverter()
        color = await conv.convert(ctx, color)

        embed.color = color.value

        while True:
            field_name = await ctx.get_input(
                "Would you like to add a field? If yes, type the name of the field.\nElse type 'no' without the cb"
            )
            if field_name.lower().startswith("no"):
                break
            if len(field_name) > 256:
                await ctx.send_line("Field name too long.")
                continue
            field_desc = await ctx.get_input("What should be the desc of the field be?")
            if len(field_desc) > 1024:
                await ctx.send_line("Field value too long.")
                continue
            inline = await ctx.get_input("Should it be inline?")
            embed.add_field(
                name=field_name,
                value=field_desc,
                inline=True if inline.lower() == "yes" else False,
            )
        thumb = await ctx.get_input(
            "What should the thumbnail be? Type `no` if you don't want one."
        )
        if not thumb.lower().startswith("no"):
            embed.set_thumbnail(url=thumb)

        img = await ctx.get_input(
            "What should the image be? Type `no` if you don't want one."
        )
        if not img.lower().startswith("no"):
            embed.set_image(url=img)
        footer = await ctx.get_input(
            "What should the footer be? Type `no` if you don't want one. "
        )
        if not footer.lower().startswith("no"):
            embed.set_footer(text=footer)
        val = embed.to_dict()
        await self.ARManager.add_ar(
            guild_id=ctx.guild.id, user_id=ctx.author.id, trigger=name, response=val
        )
        

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send_line(f"You're on cooldown. Try again in {error.retry_after:.1f} seconds.")
        else:
            # Re-raise for other handlers
            raise error

    @ar.command(aliases=["-"])
    @can_manage_msgs()
    async def remove(self, ctx, *, trigger: Union[str, int]):
        """
        Remove an AR from your guild
        """
        try:
            await self.ARManager.remove_ar(ctx.guild.id, trigger=trigger)
            await ctx.send_line("The AR was removed successfully!.")
        except TriggerDoesNotExist:
            await ctx.send_line("The AR does not exist.")


async def setup(bot):
    await bot.add_cog(Autoresponders(bot))
