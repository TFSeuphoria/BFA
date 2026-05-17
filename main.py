import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")


async def load_commands():
    for filename in os.listdir("./commands"):
        if filename.endswith(".py"):
            extension = f"commands.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"Loaded {extension}")
            except Exception as e:
                print(f"Failed to load {extension}: {e}")


async def main():
    if not TOKEN:
        print("Missing DISCORD_TOKEN in .env")
        return

    async with bot:
        await load_commands()
        await bot.start(TOKEN)


@bot.event
async def setup_hook():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


asyncio.run(main())
