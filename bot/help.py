import disnake
from disnake.ext import commands


class MyHelp(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                "help": "Help command for the bot",
                "cooldown": commands.CooldownMapping.from_cooldown(
                    1, 3, commands.BucketType.user
                ),
                "aliases": ["h"],
            }
        )

    async def send(self, **kwargs):
        await self.get_destination().send(**kwargs)

    async def send_bot_help(self, mapping):
        ctx = self.context
        em = disnake.Embed(
            title=f"{ctx.me.display_name} Help Menu",
            timestamp=ctx.message.created_at,
            color=0x2F3136,
        )
        em.set_thumbnail(url=ctx.me.avatar.url)
        usable = 0

        for cog, commands in mapping.items():
            if filtered_commands := await self.filter_commands(commands):
                amt_cmds = len(filtered_commands)
                usable += amt_cmds
                if cog:
                    name = cog.qualified_name
                    description = cog.description or "No description"
                    em.add_field(
                        name=f"{name} [{amt_cmds}]", value=description, inline=False
                    )
        em.description = f"""{len(ctx.bot.commands)} commands | {usable} usable\n\nUse "help [command | module]" for more info.\nIf you can't see any module, it means that you don't have the permission to view them.\n\n`<>` required | `[]` optional"""
        await self.send(embed=em)

    async def send_command_help(self, command):
        signature = self.get_command_signature(command)
        embed = disnake.Embed(
            title=signature,
            description=command.help or "No help found...",
            color=0x2F3136,
        )

        if cog := command.cog:
            embed.add_field(name="Category", value=cog.qualified_name, inline=False)

        can_run = "No"

        with contextlib.suppress(commands.CommandError):
            if await command.can_run(self.context):
                can_run = "Yes"

        embed.add_field(name="Usable", value=can_run, inline=False)

        if command._buckets and (cooldown := command._buckets._cooldown):
            embed.add_field(
                name="Cooldown",
                value=f"{cooldown.rate} per {cooldown.per:.0f} seconds",
                inline=False,
            )

        await self.send(embed=embed)

    async def send_help_embed(self, title, description, commands):
        embed = disnake.Embed(
            title=title, description=description or "No help found...", color=0x2F3136
        )

        if filtered_commands := await self.filter_commands(commands):
            for command in filtered_commands:
                embed.add_field(
                    name=self.get_command_signature(command),
                    value=command.help or "No help found...",
                    inline=False,
                )
        if not filtered_commands:
            await self.send("You don't have the required permissions for viewing this.")

        await self.send(embed=embed)

    async def send_group_help(self, group):
        title = self.get_command_signature(group)
        await self.send_help_embed(title, group.help, group.commands)

    async def send_cog_help(self, cog):
        title = cog.qualified_name or "No"
        em = disnake.Embed(
            title=f"{title} Category",
            description=f"{cog.description}\n\n"
            + "\n".join([f" `{x.name}` • {x.help}" for x in cog.get_commands()]),
            color=0x2F3136,
        )
        em.set_footer(text="Use help [command] for more info")
        await self.send(embed=em)

    async def send_error_message(self, error):
        channel = self.get_destination()
        await channel.send(error)
