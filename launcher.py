import os
import disnake
from dotenv import load_dotenv
import asyncio
import uvloop
from bot import BaseBot

load_dotenv()

Jihye = BaseBot(
    command_prefix="?",
    intents=disnake.Intents.all(),
    mongo_url=os.getenv("DBTOKEN"),
    db_name="rewrite",
    reload=True,
    test_guilds=[923592895162884118],
)


async def main():
    bot = Jihye
    await bot.start(os.getenv("TOKEN"))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
