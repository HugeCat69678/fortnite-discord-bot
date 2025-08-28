import os
import requests
import asyncio
import discord
from discord import app_commands
from datetime import datetime

# --- ENVIRONMENT VARIABLES ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_WEBHOOK = os.getenv("WEBHOOK_URL")
API_KEY = os.getenv("API_KEY")
GUILD_ID = int(os.getenv("GUILD_ID", 0))  # your server ID

# --- PLAYER MAPPING ---
PLAYERS = {
    "1355963578221334570": "Dov1duzass",
    "722100931164110939": "Huge_CatWasTaken"
}

API_URL = "https://fortnite-api.com/v2/stats/br/v2/{epic}"
last_match_ids = {}

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --- FUNCTION TO SEND PROFESSIONAL EMBED WITH EMOJIS ---
def send_professional_embed(user_mention, mode, queue_type, kills, placement, won, skin_url=None):
    color = 0x00ff00 if won else 0xff0000
    status_emoji = ":win:" if won else ":lose:"
    status_text = "Victory!" if won else "Defeat"
    
    embed = {
        "title": f"{status_emoji} {status_text} — {user_mention}",
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "thumbnail": {"url": skin_url} if skin_url else None,
        "fields": [
            {"name": "Game Mode", "value": mode, "inline": True},
            {"name": "Queue Type", "value": queue_type, "inline": True},
            {"name": "Eliminations", "value": f"{kills} 💥", "inline": True},
            {"name": "Placement", "value": f"{placement}" if not won else "🏆", "inline": True},
        ],
        "footer": {"text": "Fortnite Tracker 🚀"}
    }
    print(f"[Webhook] Sending embed: {status_text} for {user_mention}")
    requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})

# --- STARTUP MESSAGE ---
async def send_startup_message():
    await client.wait_until_ready()
    print("[Bot] Sending startup embed...")
    send_professional_embed("Bot Online", "N/A", "N/A", 0, 0, True)

# --- CHECK REAL FORTNITE MATCHES ---
async def check_matches_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        print("[MatchChecker] Checking Fortnite matches...")
        for discord_id, epic_name in PLAYERS.items():
            try:
                url = API_URL.format(epic=epic_name)
                res = requests.get(url, headers={"Authorization": API_KEY}).json()
                if "data" not in res:
                    print(f"[MatchChecker] No data for {epic_name}")
                    continue

                last_match = res["data"].get("lastMatch", {})
                match_id = last_match.get("id")
                if not match_id:
                    continue
                if last_match_ids.get(discord_id) == match_id:
                    continue

                last_match_ids[discord_id] = match_id

                mode = last_match.get("mode", "Unknown")       # Solo/Duo/Trio/Squad
                queue_type = last_match.get("type", "Battle Royale")
                kills = last_match.get("kills", 0)
                placement = last_match.get("placement", 99)
                won = last_match.get("victory", False)
                skin_url = last_match.get("skin", {}).get("image")
                mention = f"<@{discord_id}>"

                send_professional_embed(mention, mode, queue_type, kills, placement, won, skin_url)
                print(f"[MatchChecker] Sent match for {mention}: {'WON' if won else 'LOST'}")
            except Exception as e:
                print(f"[MatchChecker] Error for {epic_name}: {e}")
        await asyncio.sleep(60)

# --- SLASH COMMAND /cmatch ---
@tree.command(name="cmatch", description="Send a custom detailed Fortnite match")
@app_commands.describe(
    user="Discord user to mention",
    won="Did they win?",
    mode="Game mode: Solo, Duo, Trio, Squad",
    queue_type="Queue type: Battle Royale, Blitz Royale, etc.",
    kills="Number of eliminations",
    placement="Placement if lost",
    skin_url="URL of the skin thumbnail (optional)"
)
async def cmatch(interaction: discord.Interaction, user: discord.Member, won: bool, mode: str, queue_type: str, kills: int, placement: int = 0, skin_url: str = None):
    mention = f"<@{user.id}>"
    send_professional_embed(mention, mode, queue_type, kills, placement, won, skin_url)
    await interaction.response.send_message("Custom detailed match sent via webhook ✅", ephemeral=True)
    print(f"[SlashCommand] {interaction.user} sent /cmatch for {mention}")

# --- BOT READY EVENT ---
@client.event
async def on_ready():
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        await tree.sync(guild=guild)
        print(f"[Bot] Commands synced for guild {GUILD_ID}")
    else:
        await tree.sync()
        print("[Bot] Commands globally synced")
    print(f"[Bot] Online as {client.user}")
    await send_startup_message()
    client.loop.create_task(check_matches_loop())

# --- RUN BOT ---
print("[Bot] Starting...")
client.run(DISCORD_TOKEN)
