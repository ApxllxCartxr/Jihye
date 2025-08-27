import os
import discord
from dotenv import load_dotenv
import asyncio
from bot import BaseBot
import nest_asyncio
nest_asyncio.apply()


load_dotenv()

Jihye = BaseBot(
    command_prefix="?",
    intents=discord.Intents.all(),
    mongo_url=os.getenv("MONGO_URL"),
    db_name=os.getenv("DB_NAME", "rewrite"),
    reload=True,
    test_guilds=[923592895162884118],
)


async def main():
    bot = Jihye
    await bot.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
     
    loop.run_until_complete(main())
