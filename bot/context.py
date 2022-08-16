import asyncio
import disnake
from disnake.ext.commands import Context


class CustomContext(Context):
    async def send_line(self, desc, title=None, time: bool = False):
        embed = disnake.Embed(
            description=desc,
            color=0x2F3136,
            timestamp=self.message.created_at if time else disnake.Embed.Empty,
        )
        if title:
            embed.set_author(name=title)
        return await self.send(embed=embed)

    async def confirm(self, question: str, delete_after: bool = False):
        msg = await self.send_line(question)

        def check(r, u):  # r = discord.Reaction, u = discord.Member or discord.User.
            return (
                u.id == self.author.id
                and r.message.channel.id == self.channel.id
                and str(r.emoji) in ["✅", "❎"]
            )

        await msg.add_reaction("✅")
        await msg.add_reaction("❎")

        try:

            reaction, user = await self.bot.wait_for(
                event="reaction_add", check=check, timeout=60.0
            )
            # reaction = discord.Reaction, user = discord.Member or discord.User.
        except asyncio.TimeoutError:
            # at this point, the check didn't become True.
            await self.send_line(
                f"**{self.author}**, you didnt react with a ✅ or :negative_squared_cross_mark: in 60 seconds."
            )
            if delete_after:
                await msg.delete()
        else:
            if str(reaction.emoji) in "✅":
                val = True
            if str(reaction.emoji) in "❎":
                val = False
        try:
            if delete_after:
                await msg.delete()
        finally:
            return val

    async def get_input(
        self,
        desc: str,
        title: str = None,
        timeout: int = 60,
        delete_after: bool = False,
        _id=None,
    ):
        sent = await self.send_line(desc, title=title)
        val = None

        try:
            _id = _id or self.author.id or self.id
        except:
            self.send_line("Something went wrong try again. . ")

        try:
            msg = await self.bot.wait_for(
                "message",
                timeout=timeout,
                check=lambda message: message.author.id == _id,
            )

        except asyncio.TimeoutError:
            if delete_after:
                await sent.delete()
            await self.send_line("You took too long </3")

        else:
            val = msg.content

        try:
            if delete_after:
                await sent.delete()

        finally:
            return val

    async def send_basic_embed(
        self,
        desc: str,
        *,
        title=None,
        color=0x2F3136,
        img=None,
        thumb=None,
        target=None,
        footer=None,
        reply: bool = False,
        time: bool = False,
        author: bool = False,
        **kwargs,
    ):
        """Wraps a string to send formatted as an embed"""

        embed = disnake.Embed(description=desc)

        if color:
            embed.colour = color
        if title:
            embed.set_author(name=title, icon_url=self.author.avatar.url)
        if time:
            # Doesnt work on Channels, Users, Members
            embed.timestamp = self.message.created_at

        if author and not footer:
            try:
                text = self.author.display_name
                icon_url = self.author.avatar.url
            except AttributeError:
                text = self.display_name
                icon_url = self.avatar.url

            embed.set_footer(text=f"requested by {text}", icon_url=icon_url)
        if footer and not author:
            embed.set_footer(text=footer)
        if img:
            embed.set_image(url=img)

        if thumb:
            embed.set_thumbnail(url=thumb)

        await self.send(embed=embed, **kwargs)
