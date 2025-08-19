import requests
import time
import json

# Load config
with open("config.json") as f:
    config = json.load(f)

DISCORD_WEBHOOK = config["webhook_url"]
API_KEY = config["api_key"]
PLAYERS = config["players"]

API_URL = "https://fortnite-api.com/v2/stats/br/v2/{epic}"

def send_message(content: str):
    """Send a message to Discord via webhook."""
    requests.post(DISCORD_WEBHOOK, json={"content": content})

def check_matches():
    for discord_id, epic_name in PLAYERS.items():
        url = API_URL.format(epic=epic_name)
        res = requests.get(url, headers={"Authorization": API_KEY}).json()

        if "data" not in res:
            continue

        # ⚠️ Placeholder — replace with actual Fortnite API fields
        last_match = res["data"]  

        # Example values (you must adjust based on real API structure)
        won = last_match.get("lastMatch", {}).get("victory", False)
        kills = last_match.get("lastMatch", {}).get("kills", 0)
        placement = last_match.get("lastMatch", {}).get("placement", 99)
        mode = last_match.get("lastMatch", {}).get("mode", "Unknown")

        if won:
            msg = f"<@{discord_id}> has won a {mode} with {kills} eliminations! Congrats."
        else:
            msg = f"<@{discord_id}> lost a {mode} with {kills} eliminations. Placement: #{placement}"

        send_message(msg)

if __name__ == "__main__":
    while True:
        check_matches()
        time.sleep(60)  # check every 60s
