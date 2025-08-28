import requests
import time
import os

# Environment variables
DISCORD_WEBHOOK = os.getenv("WEBHOOK_URL")
API_KEY = os.getenv("API_KEY")

# Player mapping: Discord ID -> Epic Username
PLAYERS = {
    "1355963578221334570": "Dov1duzass",
    "722100931164110939": "Huge_CatWasTaken"
}

API_URL = "https://fortnite-api.com/v2/stats/br/v2/{epic}"

def send_embed(title, description, color=0x00ff00):
    """Send an embed to Discord via webhook."""
    data = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color
            }
        ]
    }
    requests.post(DISCORD_WEBHOOK, json=data)

# Send a test message when the bot starts
send_embed("Bot Online ✅", "The Fortnite → Discord bot is now running!", color=0x3498db)

def check_matches():
    for discord_id, epic_name in PLAYERS.items():
        url = API_URL.format(epic=epic_name)
        res = requests.get(url, headers={"Authorization": API_KEY}).json()

        if "data" not in res:
            continue

        # Placeholder — replace with real API response fields
        last_match = res["data"]

        won = last_match.get("lastMatch", {}).get("victory", False)
        kills = last_match.get("lastMatch", {}).get("kills", 0)
        placement = last_match.get("lastMatch", {}).get("placement", 99)
        mode = last_match.get("lastMatch", {}).get("mode", "Unknown")

        if won:
            title = f"🏆 {discord_id} WON!"
            desc = f"Mode: {mode}\nEliminations: {kills}"
            color = 0x00ff00
        else:
            title = f"💀 {discord_id} LOST"
            desc = f"Mode: {mode}\nEliminations: {kills}\nPlacement: #{placement}"
            color = 0xff0000

        send_embed(title, desc, color)

if __name__ == "__main__":
    while True:
        check_matches()
        time.sleep(60)
