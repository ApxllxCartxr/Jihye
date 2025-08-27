import discord
from discord.ext import commands
from typing import List, Union, Optional, Sequence


class SimplePaginator(discord.ui.View):
    """A minimal, plug-and-play paginator using discord.py's ui system.

    Usage (Context):
        view = SimplePaginator(pages)
        await view.send(ctx)

    Usage (Interaction):
        view = SimplePaginator(pages, author_id=ctx.author.id)
        await view.send(interaction=interaction)

    Features:
    - Pages are strings or discord.Embed instances.
    - Works with a commands.Context or discord.Interaction.
    - Optional author restriction (only author can interact).
    - Cleanly removes controls on timeout/stop.
    """

    def __init__(
        self,
        pages: Sequence[Union[str, discord.Embed]],
        *,
        author_id: Optional[int] = None,
        timeout: float = 180.0,
        allow_everyone: bool = False,
        ephemeral: bool = False,
    ):
        super().__init__(timeout=timeout)
        self._pages = list(pages)
        self._index = 0
        self.author_id = author_id
        self.allow_everyone = allow_everyone
        self.ephemeral = ephemeral

        # Buttons
        self.prev_btn = discord.ui.Button(emoji="◀", style=discord.ButtonStyle.secondary)
        self.next_btn = discord.ui.Button(emoji="▶", style=discord.ButtonStyle.secondary)
        self.page_btn = discord.ui.Button(label="0/0", style=discord.ButtonStyle.gray, disabled=True)
        self.stop_btn = discord.ui.Button(emoji="⏹️", style=discord.ButtonStyle.danger)

        # Wire callbacks
        self.prev_btn.callback = self._prev
        self.next_btn.callback = self._next
        self.stop_btn.callback = self._stop

        # Add to view
        self.add_item(self.prev_btn)
        self.add_item(self.page_btn)
        self.add_item(self.next_btn)
        self.add_item(self.stop_btn)

        self._message: Optional[discord.Message] = None
        self._update_buttons()

    @property
    def pages(self) -> List[Union[str, discord.Embed]]:
        return self._pages

    @property
    def index(self) -> int:
        return self._index

    def _update_buttons(self) -> None:
        total = len(self._pages)
        self.page_btn.label = f"{self._index + 1}/{total}"
        self.prev_btn.disabled = self._index <= 0
        self.next_btn.disabled = self._index >= max(0, total - 1)

    async def send(self, ctx: Optional[commands.Context] = None, interaction: Optional[discord.Interaction] = None, *, channel: Optional[discord.abc.Messageable] = None):
        """Send the paginator. Provide either a Context or an Interaction (or channel).

        Examples:
            await view.send(ctx)
            await view.send(interaction=interaction)
            await view.send(channel=some_channel)
        """
        if not self._pages:
            if ctx:
                await ctx.send("No content to display.")
            elif interaction:
                if interaction.response and not getattr(interaction.response, "_responded", False):
                    await interaction.response.send_message("No content to display.", ephemeral=self.ephemeral)
                else:
                    try:
                        await interaction.edit_original_response(content="No content to display.")
                    except Exception:
                        pass
            elif channel:
                await channel.send("No content to display.")
            return

        # Single page shortcut
        if len(self._pages) == 1:
            page = self._pages[0]
            if ctx:
                if isinstance(page, discord.Embed):
                    await ctx.send(embed=page)
                else:
                    await ctx.send(page)
            elif interaction:
                if isinstance(page, discord.Embed):
                    if interaction.response and not getattr(interaction.response, "_responded", False):
                        await interaction.response.send_message(embed=page, ephemeral=self.ephemeral)
                        self._message = await interaction.original_response()
                    else:
                        try:
                            await interaction.edit_original_response(embed=page)
                            self._message = await interaction.original_response()
                        except Exception:
                            pass
                else:
                    if interaction.response and not getattr(interaction.response, "_responded", False):
                        await interaction.response.send_message(content=page, ephemeral=self.ephemeral)
                        self._message = await interaction.original_response()
                    else:
                        try:
                            await interaction.edit_original_response(content=page)
                            self._message = await interaction.original_response()
                        except Exception:
                            pass
            elif channel:
                if isinstance(page, discord.Embed):
                    await channel.send(embed=page)
                else:
                    await channel.send(page)
            return

        # Multi-page send
        page = self._pages[self._index]
        if ctx:
            if isinstance(page, discord.Embed):
                self._message = await ctx.send(embed=page, view=self)
            else:
                self._message = await ctx.send(page, view=self)
        elif interaction:
            if isinstance(page, discord.Embed):
                if interaction.response and not getattr(interaction.response, "_responded", False):
                    await interaction.response.send_message(embed=page, view=self, ephemeral=self.ephemeral)
                    self._message = await interaction.original_response()
                else:
                    try:
                        await interaction.edit_original_response(embed=page, view=self)
                        self._message = await interaction.original_response()
                    except Exception:
                        pass
            else:
                if interaction.response and not getattr(interaction.response, "_responded", False):
                    await interaction.response.send_message(content=page, view=self, ephemeral=self.ephemeral)
                    self._message = await interaction.original_response()
                else:
                    try:
                        await interaction.edit_original_response(content=page, view=self)
                        self._message = await interaction.original_response()
                    except Exception:
                        pass
        elif channel:
            if isinstance(page, discord.Embed):
                self._message = await channel.send(embed=page, view=self)
            else:
                self._message = await channel.send(page, view=self)

    async def _prev(self, interaction: discord.Interaction):
        if not self._can_interact(interaction):
            await interaction.response.defer()
            return
        if self._index > 0:
            self._index -= 1
            self._update_buttons()
            await self._edit(interaction)

    async def _next(self, interaction: discord.Interaction):
        if not self._can_interact(interaction):
            await interaction.response.defer()
            return
        if self._index < len(self._pages) - 1:
            self._index += 1
            self._update_buttons()
            await self._edit(interaction)

    async def _stop(self, interaction: discord.Interaction):
        if not self._can_interact(interaction):
            await interaction.response.defer()
            return
        await interaction.response.defer()
        if self._message:
            try:
                await self._message.edit(view=None)
            except discord.NotFound:
                pass
        self.stop()

    async def _edit(self, interaction: discord.Interaction):
        page = self._pages[self._index]
        try:
            if isinstance(page, discord.Embed):
                await interaction.response.edit_message(embed=page, view=self)
            else:
                await interaction.response.edit_message(content=page, view=self)
        except Exception:
            # Fallback: edit stored message directly
            if self._message:
                if isinstance(page, discord.Embed):
                    await self._message.edit(embed=page, view=self)
                else:
                    await self._message.edit(content=page, view=self)

    def _can_interact(self, interaction: discord.Interaction) -> bool:
        if self.allow_everyone:
            return True
        if self.author_id is None:
            return True
        return interaction.user.id == self.author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self._can_interact(interaction)

    async def on_timeout(self) -> None:
        if self._message:
            try:
                await self._message.edit(view=None)
            except discord.NotFound:
                pass


# Backwards compatibility
Paginator = SimplePaginator
