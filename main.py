import discord
from discord.ext import commands

TOKEN = "your_token_here"
MOD_CHANNEL_ID = 1362997933552959558
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is ready: {bot.user}")

@bot.tree.command(name="promptcode")
async def promptcode(interaction: discord.Interaction):
    try:
        # Acknowledge the interaction once, to prevent timeout errors
        await interaction.response.defer(ephemeral=True)

        # Send a DM to the user
        user = interaction.user
        try:
            await user.send("Please check your email for the 6-digit code and reply with it here.")
            await interaction.followup.send("✅ Prompt sent. Please check your DM.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ Couldn't send DM. Please make sure your DMs are open.", ephemeral=True)

    except Exception as e:
        print(f"Error in promptcode command: {e}")

bot.run(TOKEN)
