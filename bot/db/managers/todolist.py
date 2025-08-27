from bot.db import MongoManager
from copy import deepcopy
from pprint import pprint
from bot.exceptions import TaskExists, TaskDoesNotExist
from discord.ext.commands import Paginator
import datetime


class ToDoListManager:
    def __init__(self, db: MongoManager):
        self.db = db
        self.cached = False

    async def initialize(self) -> None:
        self.to_do_list = dict()
        to_do_lists = await self.db.todolist.get_all()
        for user in to_do_lists:
            self.to_do_list[user["_id"]] = user
        self.cached = True

    async def add_task(self, user_id, task: str):
        timestamp = datetime.datetime.now()
        task = f"{task}\n||*(added <t:{timestamp.timestamp():.0f}:R>)*||"
        if self.cached:
            if user_id in self.to_do_list:
                tempdict = deepcopy(self.to_do_list[user_id])

                if task in tempdict["tasks"]:
                    raise TaskExists

                tempdict["tasks"].append(task)

            else:
                tempdict = {"_id": user_id, "tasks": [task]}

            self.to_do_list[user_id] = tempdict
            await self.db.todolist.upsert(tempdict)
            return
        else:
            taskdict = await self.db.todolist.find({"_id": user_id})
            taskdict["tasks"].append(task)
            await self.db.todolist.upsert(taskdict)
            return

    async def remove_task(self, user_id, task: int):
        if self.cached:
            if user_id not in self.to_do_list:
                raise TaskDoesNotExist

            tempdict = deepcopy(self.to_do_list[user_id])

            try:
                tempdict["tasks"].pop(task)
            except IndexError:
                raise TaskDoesNotExist

            self.to_do_list[user_id] = tempdict
            await self.db.todolist.upsert(tempdict)
        else:
            taskdict = await self.db.todolist.find({"_id": user_id})
            try:
                tempdict["tasks"].pop(task)
            except IndexError:
                raise TaskDoesNotExist
            await self.db.todolist.upsert(taskdict)

    async def clear_all(self, user_id):
        if self.cached:
            if user_id not in self.to_do_list:
                raise TaskDoesNotExist
            if not self.to_do_list[user_id]["tasks"]:
                raise TaskDoesNotExist

            tempdict = deepcopy(self.to_do_list[user_id])
            tempdict["tasks"] = []

            self.to_do_list[user_id] = tempdict
            await self.db.todolist.upsert(tempdict)
            return
        else:
            taskdict = await self.db.todolist.find({"_id": user_id})
            taskdict["tasks"] = []
            await self.db.todolist.upsert(taskdict)

    async def fetch_tasks(self, user_id) -> str:
        if self.cached:
            if not self.to_do_list[user_id]["tasks"]:
                text = "You have no tasks."
            else:
                pages = Paginator(prefix="", suffix="")
                for i, t in enumerate(self.to_do_list[user_id]["tasks"]):
                    pages.add_line(f"**({i+1})** **     **{t}")

                text = pages.pages[0]

            return text
        else:
            taskdict = await self.db.todolist.find({"_id": user_id})

            if not taskdict["tasks"]:
                text = "You have no tasks."
            else:
                pages = Paginator(prefix="", suffix="")
                for i, t in enumerate(taskdict["tasks"]):
                    pages.add_line(f"**({i+1})** **     **{t}")

                text = pages.pages[0]

            return text