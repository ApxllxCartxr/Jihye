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

    async def get_input(
        self,
        desc,
        title=None,
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
            if msg:
                val = msg.content
        except asyncio.TimeoutError:
            if delete_after:
                await sent.delete()

            return val

        try:
            if delete_after:
                await sent.delete()
                await msg.delete()
        finally:
            return val

    async def send_basic_embed(
        self,
        desc: str,
        *,
        color=0x2F3136,
        img=None,
        thumb=None,
        target=None,
        reply: bool = False,
        time: bool = False,
        author: bool = False,
        **kwargs,
    ):
        """Wraps a string to send formatted as an embed"""

        embed = disnake.Embed(description=desc)

        if color:
            embed.colour = color

        if time:
            # Doesnt work on Channels, Users, Members
            embed.timestamp = self.message.created_at

        if author:
            try:
                text = self.author.display_name
                icon_url = self.author.avatar.url
            except AttributeError:
                text = self.display_name
                icon_url = self.avatar.url

            embed.set_footer(text=text, icon_url=icon_url)

        if img:
            embed.set_image(url=img)

        if thumb:
            embed.set_thumbnail(url=thumb)

        await self.send(embed=embed)
