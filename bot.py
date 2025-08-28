import os
import requests
import asyncio
import discord

# Environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Bot token
DISCORD_WEBHOOK = os.getenv("WEBHOOK_URL")  # Webhook URL
API_KEY = os.getenv("API_KEY")  # Fortnite API key

# Player mapping: Discord ID -> Epic Username
PLAYERS = {
    "1355963578221334570": "Dov1duzass",
    "722100931164110939": "Huge_CatWasTaken"
}

API_URL = "https://fortnite-api.com/v2/stats/br/v2/{epic}"

# Track last match IDs per player
last_match_ids = {}

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

def send_embed(title, description, color=0x00ff00):
    """Send embed via webhook."""
    data = {"embeds": [{"title": title, "description": description, "color": color}]}
    requests.post(DISCORD_WEBHOOK, json=data)

async def check_matches_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        for discord_id, epic_name in PLAYERS.items():
            url = API_URL.format(epic=epic_name)
            res = requests.get(url, headers={"Authorization": API_KEY}).json()

            if "data" not in res:
                continue

            # Assume lastMatch contains: id, mode, kills, placement, victory
            last_match = res["data"].get("lastMatch", {})
            match_id = last_match.get("id")
            if not match_id:
                continue

            if last_match_ids.get(discord_id) == match_id:
                continue

            last_match_ids[discord_id] = match_id

            mode = last_match.get("mode", "Unknown")  # Solo, Duo, Trio, Squad
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

@client.event
async def on_ready():
    print(f"Bot online as {client.user}")
    send_embed("Bot Online ✅", "The Fortnite → Discord bot is now running!", color=0x3498db)
    client.loop.create_task(check_matches_loop())

client.run(DISCORD_TOKEN)
