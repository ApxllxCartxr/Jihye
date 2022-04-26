import os

# import asyncio
# import uvloop
import disnake
from dotenv import load_dotenv
from bot import Bot

load_dotenv()

Jihye = Bot(
    command_prefix="?",
    intents=disnake.Intents.all(),
    mongo_url=os.getenv("DBTOKEN"),
    dbname="rewrite",
    reload=True,
    #    intents=disnake.Intents.all,
)


def main():
    bot = Jihye
    bot.run(os.getenv("TOKEN"))


if __name__ == "__main__":
    # uvloop.install()
    main()
