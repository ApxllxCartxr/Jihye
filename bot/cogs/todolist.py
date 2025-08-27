from discord.ext import commands, tasks
from bot.exceptions import TaskExists, TaskDoesNotExist
from bot.db.managers import ToDoListManager
import logging

log = logging.getLogger(__name__)


class ToDoList(commands.Cog):
    """This module contains all the notes/to do list cmds\n"""

    def __init__(self, bot):
        self.bot = bot
        self.connect_to_do_list.start()

    @tasks.loop(count=1)
    async def connect_to_do_list(self):
        await self.bot.wait_until_ready()
        self.ToDoListManager = ToDoListManager(self.bot.db)
        await self.ToDoListManager.initialize()
        log.info("ToDoListManager has been initialized.")

    @commands.group(aliases=["tdl", "tasks"], invoke_without_command=True)
    async def todolist(self, ctx):
        """Shows all your current tasks"""
        tdlist = await self.ToDoListManager.fetch_tasks(str(ctx.author.id))
        await ctx.send_basic_embed(
            tdlist,
            title=f"{ctx.author.name}'s to do list.",
        )

    @todolist.command(
        aliases=["+"],
    )
    async def add(self, ctx, *, task):
        """Add a new task to your list"""
        try:
            await self.ToDoListManager.add_task(str(ctx.author.id), task)
            tdlist = await self.ToDoListManager.fetch_tasks(str(ctx.author.id))
            await ctx.send_basic_embed(
                tdlist,
                title=f"{ctx.author.name}'s to do list.",
                content=f"New task was added!",
            )
        except TaskExists:
            await ctx.send_line("This already exists in your list.")

    @todolist.command(
        aliases=[
            "-",
        ]
    )
    async def remove(self, ctx, task: int):
        """Remove a certain task from your list"""
        try:
            await self.ToDoListManager.remove_task(str(ctx.author.id), task - 1)
            tdlist = await self.ToDoListManager.fetch_tasks(str(ctx.author.id))
            await ctx.send_basic_embed(
                tdlist,
                title=f"{ctx.author.name}'s to do list.",
                content="Task was removed!",
            )
        except TaskDoesNotExist:
            await ctx.send_line("Task does not even exist")

    @todolist.command(aliases=["clear all", "clearall", "reset"])
    async def clear(self, ctx):
        """Clear your list entirely"""
        try:
            await self.ToDoListManager.clear_all(str(ctx.author.id))
            inp = await ctx.get_input(
                "Are you sure you want to clear all tasks?\n (**y**~~our~~/**n**~~ame~~)"
            )
            if inp.lower() == "y" or inp.lower() == "yes":
                await ctx.send_line("All your tasks were cleared.")
            else:
                await ctx.send_line("Get out then")
        except TaskDoesNotExist:
            await ctx.send_line("You don't have any tasks.")

    @commands.command()
    async def uptime(self, ctx):
        await ctx.send_line(f"<t:{self.bot.uptime.timestamp():.0f}:R>")


async def setup(bot):
    await bot.add_cog(ToDoList(bot))