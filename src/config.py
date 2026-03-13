import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LEAGUE_ID = int(os.getenv("LEAGUE_ID", 71))
SEASON = int(os.getenv("SEASON", 2024))

# ---------------------------------------------------------
# CONEXÃO DIRETA API-SPORTS (Sem passar pelo RapidAPI)
# ---------------------------------------------------------
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}
