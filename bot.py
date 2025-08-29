import os
import datetime
import requests
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread

# -------------------------------
# Flask Keep-Alive Server
# -------------------------------
app = Flask('')

@app.route('/')
def home():
    return "Fortnite Tracker 🚀 is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# -------------------------------
# Discord Bot Setup
# -------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")  # your bot token in Render env vars
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # webhook URL for match results

intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)

# -------------------------------
# Events
# -------------------------------
@client.event
async def on_ready():
    print(f"[Bot] Logged in as {client.user} ✅")
    channel = discord.utils.get(client.get_all_channels(), name="general")  # Change if needed
    if channel:
        await channel.send("✅ **Bot Online!** 🚀")

    # Test API connection
    try:
        resp = requests.get("https://fortniteapi.io/v1/status", headers={"Authorization": "static-token"})
        if resp.status_code == 200:
            await channel.send("🌐 Connected to Fortnite API successfully!")
            print("[Bot] Fortnite API connection successful ✅")
        else:
            await channel.send("⚠️ Failed to connect to Fortnite API.")
            print("[Bot] Fortnite API connection failed ❌")
    except Exception as e:
        await channel.send("❌ Fortnite API connection error.")
        print(f"[Bot] API error: {e}")

# -------------------------------
# Slash Command: /cmatch
# -------------------------------
@client.tree.command(name="cmatch", description="Post a custom Fortnite match result.")
@app_commands.describe(
    result="Did you win or lose?",
    user="Which user played?",
    mode="Solo, Duo, Trio, Squad",
    gametype="Battle Royale, Blitz Royale, etc.",
    placement="Placement if lost (e.g., 5th)",
    kills="Number of kills",
    skin="Skin worn in the match (image URL)"
)
async def cmatch(interaction: discord.Interaction, result: str, user: str, mode: str, gametype: str, placement: str, kills: int, skin: str):
    print(f"[Bot] /cmatch command used by {interaction.user}")

    # Emoji
    emoji = "🏆" if result.lower() == "won" else "💀"

    # Embed
    embed = discord.Embed(
        title=f"Fortnite Tracker 🚀 - Match Result",
        description=f"{emoji} **{user}** has finished a match!",
        color=discord.Color.green() if result.lower() == "won" else discord.Color.red(),
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.add_field(name="🎮 Game Mode", value=mode, inline=True)
    embed.add_field(name="🗺️ Type", value=gametype, inline=True)
    embed.add_field(name="📊 Result", value=result, inline=True)
    embed.add_field(name="📍 Placement", value=placement, inline=True)
    embed.add_field(name="🔫 Kills", value=str(kills), inline=True)
    embed.set_footer(text="Fortnite Tracker 🚀 | Powered by Discord")
    embed.set_thumbnail(url=skin)

    # Send via webhook
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"embeds": [embed.to_dict()]})
        await interaction.response.send_message("✅ Match result sent via webhook!", ephemeral=True)
        print("[Bot] Match result sent to webhook.")
    else:
        await interaction.response.send_message("⚠️ Webhook not configured.", ephemeral=True)
        print("[Bot] Webhook missing ❌")

# -------------------------------
# Run bot
# -------------------------------
keep_alive()
client.run(TOKEN)
