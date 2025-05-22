import discord
from discord.ext import commands
import json

# Load fruit stock from JSON file
with open('fruit_stock.json', 'r') as f:
    fruit_stock = json.load(f)

# Set up bot with required intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.command(name='stock')
async def stock(ctx):
    if not fruit_stock:
        await ctx.send("No stock available.")
        return

    message = "**Current Stock:**\n"
    for item in fruit_stock:
        traits = ", ".join(item["traits"])
        value = item["value"]
        message += f"- {traits} )- {value}\n"

    # Split message if too long for Discord
    for chunk in [message[i:i+1900] for i in range(0, len(message), 1900)]:
        await ctx.send(chunk)

bot.run('YOUR_BOT_TOKEN')
