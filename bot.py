import os
import requests
import asyncio
import discord
from discord import app_commands

# --- ENVIRONMENT VARIABLES ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_WEBHOOK = os.getenv("WEBHOOK_URL")
API_KEY = os.getenv("API_KEY")
GUILD_ID = int(os.getenv("GUILD_ID", 0))

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

# --- HELPER FUNCTION TO SEND DETAILED EMBED ---
def send_detailed_embed(title, user, mode, queue_type, kills, placement, won, skin_url=None):
    color = 0x00ff00 if won else 0xff0000
    desc = f"**Queue Type:** {queue_type}\n**Game Mode:** {mode}\n**Eliminations:** {kills}"
    if not won:
        desc += f"\n**Placement:** #{placement}"
    data = {
        "embeds": [{
            "title": title,
            "description": desc,
            "color": color,
            "thumbnail": {"url": skin_url} if skin_url else None
        }]
    }
    print(f"[Webhook] Sending embed: {title}")
    requests.post(DISCORD_WEBHOOK, json=data)

# --- STARTUP ---
async def send_startup_message():
    await client.wait_until_ready()
    send_detailed_embed("Bot Online ✅", user=None, mode="N/A", queue_type="N/A", kills=0, placement=0, won=True)

# --- CHECK REAL MATCHES ---
async def check_matches_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        for discord_id, epic_name in PLAYERS.items():
            try:
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

                mode = last_match.get("mode", "Unknown")       # Solo/Duo/Trio/Squad
                queue_type = last_match.get("type", "Battle Royale") # Queue type
                kills = last_match.get("kills", 0)
                placement = last_match.get("placement", 99)
                won = last_match.get("victory", False)
                skin_url = last_match.get("skin", {}).get("image") # example, depends on API
                mention = f"<@{discord_id}>"
                title = f"🏆 {mention} WON!" if won else f"💀 {mention} LOST"
                send_detailed_embed(title, mention, mode, queue_type, kills, placement, won, skin_url)
            except Exception as e:
                print(f"[MatchChecker] Error checking match for {epic_name}: {e}")
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
    title = f"🏆 {mention} WON!" if won else f"💀 {mention} LOST"
    send_detailed_embed(title, mention, mode, queue_type, kills, placement, won, skin_url)
    await interaction.response.send_message("Custom detailed match sent via webhook ✅", ephemeral=True)
    print(f"[SlashCommand] {interaction.user} sent /cmatch for {mention}")

# --- ON READY ---
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
