import os
import requests
import asyncio
import discord
from discord import app_commands

# --- ENVIRONMENT VARIABLES ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Bot token
DISCORD_WEBHOOK = os.getenv("WEBHOOK_URL")  # Webhook URL
API_KEY = os.getenv("API_KEY")              # Fortnite API key
GUILD_ID = int(os.getenv("GUILD_ID", 0))   # Your server ID for guild-specific slash commands

# --- PLAYER MAPPING ---
PLAYERS = {
    "1355963578221334570": "Dov1duzass",
    "722100931164110939": "Huge_CatWasTaken"
}

API_URL = "https://fortnite-api.com/v2/stats/br/v2/{epic}"
last_match_ids = {}  # Track last match per player

# --- DISCORD CLIENT & SLASH COMMANDS ---
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --- FUNCTION TO SEND EMBED VIA WEBHOOK ---
def send_embed(title, description, color=0x00ff00):
    data = {"embeds": [{"title": title, "description": description, "color": color}]}
    requests.post(DISCORD_WEBHOOK, json=data)

# --- STARTUP MESSAGE ---
async def send_startup_message():
    await client.wait_until_ready()
    send_embed("Bot Online ✅", "The Fortnite → Discord bot is now running!", color=0x3498db)

# --- CHECK REAL FORTNITE MATCHES ---
async def check_matches_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        for discord_id, epic_name in PLAYERS.items():
            url = API_URL.format(epic=epic_name)
            res = requests.get(url, headers={"Authorization": API_KEY}).json()

            if "data" not in res:
                continue

            last_match = res["data"].get("lastMatch", {})
            match_id = last_match.get("id")
            if not match_id:
                continue
            if last_match_ids.get(discord_id) == match_id:
                continue

            last_match_ids[discord_id] = match_id

            mode = last_match.get("mode", "Unknown")  # Solo/Duo/Trio/Squad
            kills = last_match.get("kills", 0)
            placement = last_match.get("placement", 99)
            won = last_match.get("victory", False)
            mention = f"<@{discord_id}>"

            if won:
                title = f"🏆 {mention} WON!"
                desc = f"Mode: {mode}\nEliminations: {kills}\nPlacement: #{placement}"
                color = 0x00ff00
            else:
                title = f"💀 {mention} LOST"
                desc = f"Mode: {mode}\nEliminations: {kills}\nPlacement: #{placement}"
                color = 0xff0000

            send_embed(title, desc, color)
        await asyncio.sleep(60)

# --- SLASH COMMAND: /cmatch ---
@tree.command(name="cmatch", description="Send a custom Fortnite match message via webhook")
@app_commands.describe(
    user="The user to mention",
    won="Did they win?",
    mode="Game mode: Solo, Duo, Trio, Squad",
    kills="Number of eliminations",
    placement="Placement if lost"
)
async def cmatch(interaction: discord.Interaction, user: discord.Member, won: bool, mode: str, kills: int, placement: int = 0):
    mention = f"<@{user.id}>"
    if won:
        title = f"🏆 {mention} WON!"
        desc = f"Mode: {mode}\nEliminations: {kills}"
        color = 0x00ff00
    else:
        title = f"💀 {mention} LOST"
        desc = f"Mode: {mode}\nEliminations: {kills}\nPlacement: #{placement}"
        color = 0xff0000

    send_embed(title, desc, color)
    await interaction.response.send_message("Custom match sent via webhook ✅", ephemeral=True)

# --- BOT READY EVENT ---
@client.event
async def on_ready():
    # Register commands for guild only (fast)
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        await tree.sync(guild=guild)
    else:
        await tree.sync()  # Global (slower)
    print(f"Bot online as {client.user}")
    await send_startup_message()
    client.loop.create_task(check_matches_loop())

# --- RUN BOT ---
client.run(DISCORD_TOKEN)
