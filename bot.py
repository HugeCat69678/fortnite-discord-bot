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

# --- DISCORD CLIENT & SLASH COMMANDS ---
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --- FUNCTION TO SEND EMBED VIA WEBHOOK ---
def send_embed(title, description, color=0x00ff00):
    print(f"[Webhook] Sending embed: {title}")
    data = {"embeds": [{"title": title, "description": description, "color": color}]}
    requests.post(DISCORD_WEBHOOK, json=data)

# --- STARTUP MESSAGE ---
async def send_startup_message():
    await client.wait_until_ready()
    print("[Bot] Sending startup embed...")
    send_embed("Bot Online ✅", "The Fortnite → Discord bot is now running!", color=0x3498db)

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

                mode = last_match.get("mode", "Unknown")
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
                print(f"[MatchChecker] Sent match for {mention}: {'WON' if won else 'LOST'}")
            except Exception as e:
                print(f"[MatchChecker] Error checking match for {epic_name}: {e}")
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
    print(f"[SlashCommand] {interaction.user} used /cmatch for {user}")
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
    print(f"[SlashCommand] Embed sent for {mention}: {'WON' if won else 'LOST'}")

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
