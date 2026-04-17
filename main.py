from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import json
from dotenv import load_dotenv
import asyncio
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# =========================
# 🔐 CONFIG
# =========================

load_dotenv()

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("RIOT_API_KEY")

if not API_KEY:
    raise Exception("Falta RIOT_API_KEY en .env")

HEADERS = {"X-Riot-Token": API_KEY}

REGION = "americas"
PLATFORM = "la2"

# --- PERSISTENCIA ---
PLAYERS_FILE = "players.json"

def load_players():
    if os.path.exists(PLAYERS_FILE):
        with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Lista por defecto si el archivo no existe aún
    return [
        "YutaOkkotsuu#Maki", "Linling#XXX", "Tony#PAD", "zero#XEJG",
        "Noiserfel#LAS", "Luzbee#LAS", "Piledriver#LAS", "G4UG3N#LAS", "Askin7x#LAS"
    ]

def save_players_to_disk(players_list):
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(players_list, f, ensure_ascii=False, indent=4)

players = load_players()

class PlayerModel(BaseModel):
    name: str

# =========================
# 🔎 RIOT API (Tus Funciones Modulares)
# =========================

async def get_puuid(gameName, tagLine):
    url = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=HEADERS)
        if res.status_code != 200:
            return None
        return res.json().get("puuid")

async def get_summoner(puuid):
    url = f"https://{PLATFORM}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=HEADERS)
        if res.status_code != 200:
            return None
        return res.json()

async def get_rank(puuid):
    url = f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=HEADERS)
        if res.status_code != 200:
            return None
        data = res.json()
        for q in data:
            if q["queueType"] == "RANKED_SOLO_5x5":
                return q
    return None

TIER_ORDER = {
    "IRON": 0, "BRONZE": 1, "SILVER": 2, "GOLD": 3,
    "PLATINUM": 4, "EMERALD": 5, "DIAMOND": 6,
    "MASTER": 7, "GRANDMASTER": 8, "CHALLENGER": 9
}

RANK_ORDER = {"IV": 0, "III": 1, "II": 2, "I": 3}

def sort_players(data):
    return sorted(
        data,
        key=lambda x: (
            TIER_ORDER.get(x["tier"], -1),
            RANK_ORDER.get(x["rank"], -1),
            x["lp"]
        ),
        reverse=True
    )

# =========================
# 🚀 API
# =========================

@app.get("/ranking")
async def ranking():
    result = []
    for player in players:
        try:
            gameName, tagLine = player.split("#")
            puuid = await get_puuid(gameName, tagLine)
            if not puuid:
                continue

            summoner = await get_summoner(puuid)
            icon = summoner["profileIconId"] if summoner else 29

            rank = await get_rank(puuid)

            if rank:
                result.append({
                    "name": player,
                    "tier": rank["tier"],
                    "rank": rank["rank"],
                    "lp": rank["leaguePoints"],
                    "icon": icon
                })
            else:
                result.append({
                    "name": player,
                    "tier": "UNRANKED",
                    "rank": "",
                    "lp": 0,
                    "icon": icon
                })

            await asyncio.sleep(0.3)
        except Exception as e:
            print(f"Error procesando a un jugador: {e}")

    return sort_players(result)

@app.post("/add-player")
async def add_player(player_data: PlayerModel):
    if "#" not in player_data.name:
        return {"status": "error", "message": "Formato: Nombre#Tag"}
    
    if player_data.name not in players:
        players.append(player_data.name)
        save_players_to_disk(players)
        return {"status": "success", "message": f"{player_data.name} agregado!"}
    return {"status": "warning", "message": "Ya está en la lista"}

@app.post("/remove-player")
async def remove_player(player_data: PlayerModel):
    if player_data.name in players:
        players.remove(player_data.name)
        save_players_to_disk(players)
        return {"status": "success", "message": f"{player_data.name} eliminado!"}
    return {"status": "error", "message": "No se encontró al jugador"}

# =========================
# 🌐 FRONTEND
# =========================

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # Evitar interferencias con las rutas de la API
    if full_path.startswith("static") or full_path in ["ranking", "add-player", "remove-player"]:
        return None
    
    return FileResponse("static/index.html")