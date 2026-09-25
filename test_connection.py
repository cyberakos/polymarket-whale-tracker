"""Közvetlen API kapcsolat-tesztelő szkript."""

import httpx

GAMMA_URL = "https://gamma-api.polymarket.com/markets?closed=false&limit=3"
# A helyes végpont a /v1/leaderboard paraméterekkel:
DATA_URL = (
    "https://data-api.polymarket.com/v1/leaderboard"
    "?category=OVERALL&timePeriod=ALL&orderBy=PNL&limit=5"
)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

print("1. Gamma API tesztelése...")
try:
    r = httpx.get(GAMMA_URL, headers=headers, timeout=10.0)
    print(f"-> Gamma API Státuszkód: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"-> Siker! Első aktív piac címe: {data[0].get('question')}")
    else:
        print(f"-> Válasz: {r.text[:200]}")
except Exception as e:
    print(f"-> Gamma API hiba: {e}")

print("\n2. Data API (Leaderboard) tesztelése...")
try:
    r = httpx.get(DATA_URL, headers=headers, timeout=10.0)
    print(f"-> Data API Státuszkód: {r.status_code}")
    if r.status_code == 200:
        items = r.json()
        if isinstance(items, dict):
            items = items.get("data", [])
        print(f"-> Siker! #1 Bálna neve: {items[0].get('userName') or 'N/A'}")
        print(f"-> #1 Bálna címe: {items[0].get('proxyWallet')}")
        print(f"-> #1 Bálna PnL: ${float(items[0].get('pnl', 0)):,.2f}")
    else:
        print(f"-> Válasz: {r.text[:200]}")
except Exception as e:
    print(f"-> Data API hiba: {e}")