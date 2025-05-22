import discord
from discord.ext import commands
import json
import os

TOKEN = 'DISCORD_TOKEN'  # Put your bot token here

DATA_FILE = 'fruit_stock.json'

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        fruit_stock = json.load(f)
else:
    fruit_stock = {}

bot = commands.Bot(command_prefix='!')

def save_stock():
    with open(DATA_FILE, 'w') as f:
        json.dump(fruit_stock, f, indent=4)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

def create_embed(title, description, color=0x2ecc71):
    return discord.Embed(title=title, description=description, color=color)

@bot.command(name='addfruit')
async def add_fruit(ctx, fruit: str, quantity: int):
    fruit = fruit.lower()
    if fruit in fruit_stock:
        fruit_stock[fruit] += quantity
    else:
        fruit_stock[fruit] = quantity
    save_stock()

    embed = create_embed(
        title="Fruit Added 🍎",
        description=f"Added **{quantity}** {fruit}(s).\nNew total: **{fruit_stock[fruit]}**"
    )
    await ctx.send(embed=embed)

@bot.command(name='removefruit')
async def remove_fruit(ctx, fruit: str, quantity: int):
    fruit = fruit.lower()
    if fruit not in fruit_stock:
        embed = create_embed(
            title="Error ❌",
            description=f"No **{fruit}** found in stock.",
            color=0xe74c3c
        )
        await ctx.send(embed=embed)
        return

    if fruit_stock[fruit] < quantity:
        embed = create_embed(
            title="Error ❌",
            description=f"Not enough **{fruit}** to remove. You have **{fruit_stock[fruit]}**.",
            color=0xe74c3c
        )
        await ctx.send(embed=embed)
        return

    fruit_stock[fruit] -= quantity
    if fruit_stock[fruit] == 0:
        del fruit_stock[fruit]
    save_stock()

    embed = create_embed(
        title="Fruit Removed 🍏",
        description=f"Removed **{quantity}** {fruit}(s).\nNew total: **{fruit_stock.get(fruit, 0)}**"
    )
    await ctx.send(embed=embed)

@bot.command(name='stock')
async def stock(ctx):
    if not fruit_stock:
        embed = create_embed(
            title="Fruit Stock",
            description="Your fruit stock is empty.",
            color=0xf1c40f
        )
        await ctx.send(embed=embed)
        return

    description = ""
    for fruit, qty in fruit_stock.items():
        description += f"**{fruit.capitalize()}**: {qty}\n"

    embed = create_embed(
        title="Current Fruit Stock 🍇",
        description=description
    )
    await ctx.send(embed=embed)

@bot.command(name='resetstock')
async def reset_stock(ctx):
    fruit_stock.clear()
    save_stock()
    embed = create_embed(
        title="Fruit Stock Reset",
        description="Your fruit stock has been cleared.",
        color=0xe67e22
    )
    await ctx.send(embed=embed)

bot.run(TOKEN)
