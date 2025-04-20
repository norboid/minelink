import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()  # Load from .env if running locally

TOKEN = os.getenv("DISCORD_TOKEN")  # Loaded from environment variable (Render will inject this)

intents = discord.Intents.default()
intents.message_content = True  # Enable if your bot needs to read messages

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

bot.run(TOKEN)
