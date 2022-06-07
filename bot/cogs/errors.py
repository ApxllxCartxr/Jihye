import disnake
import traceback
import sys
from disnake.ext import commands
from bot.exceptions import ReactionExists, ReactionDoesNotExists


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if hasattr(ctx.command, "on_error"):
            return

        cog = ctx.cog

        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = commands.CommandNotFound

        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f"{ctx.command} has been disabled.")

        elif isinstance(error, ReactionExists):
            await ctx.send_line(f"The reaction for that role already exists")

        elif isinstance(error, ReactionDoesNotExists):
            await ctx.send_line(f"The reaction for that role does exists")

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(
                    f"{ctx.command} can not be used in Private Messages."
                )
            except disnake.HTTPException:
                pass

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print(
                "Ignoring exception in command {}:".format(ctx.command), file=sys.stderr
            )
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
