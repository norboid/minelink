import os
import random
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
VERIFICATION_CHANNEL_ID = 1362951881827160295
MOD_CHANNEL_ID = 1362997933552959558

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Store codes in memory (temporary)
user_codes = {}

class VerifyModal(discord.ui.Modal, title="Link Your Minecraft Account"):
    email = discord.ui.TextInput(label="Minecraft Email", placeholder="example@gmail.com", required=True)
    ign = discord.ui.TextInput(label="Minecraft IGN", placeholder="YourInGameName", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # Generate 6-digit code
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        user_codes[interaction.user.id] = code

        try:
            await interaction.user.send(f"Your 6-digit verification code is: **{code}**\nUse `/verifycode <code>` to complete verification.")
            await interaction.response.send_message("✅ Check your DMs for your verification code!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I couldn't send you a DM. Please enable DMs and try again.", ephemeral=True)

class LinkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Link Account", style=discord.ButtonStyle.primary)
    async def link_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())

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

@bot.tree.command(name="setup", description="Start the Minecraft account verification process")
async def setup(interaction: discord.Interaction):
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
    await interaction.response.send_message(embed=embed, view=LinkView(), ephemeral=True)

@bot.tree.command(name="verifycode", description="Submit your 6-digit verification code")
async def verifycode(interaction: discord.Interaction, code: str):
    correct_code = user_codes.get(interaction.user.id)

    if correct_code is None:
        await interaction.response.send_message("❌ You have not started verification yet.", ephemeral=True)
        return

    if code == correct_code:
        del user_codes[interaction.user.id]

        log_channel = await bot.fetch_channel(MOD_CHANNEL_ID)
        embed = discord.Embed(title="🔑 User Verified", color=discord.Color.orange())
        embed.add_field(name="User", value=interaction.user.mention, inline=False)
        embed.add_field(name="Code", value=code, inline=False)
        await log_channel.send(embed=embed)

        await interaction.response.send_message("✅ Verification successful!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Invalid code. Try again.", ephemeral=True)

bot.run(TOKEN)
