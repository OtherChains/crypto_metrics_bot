#!/usr/bin/env python3
"""
Push daily crypto-market proxy metrics into a Notion database.

Environment variables expected by the script (set in GitHub > Settings > Secrets > Actions):
  NOTION_TOKEN  – Internal Integration Secret (secret_xxx / ntn_xxx)
  NOTION_DB     – 32-character database ID of your dashboard table
"""

import os
import json
import datetime as dt
import requests
from notion_client import Client

# ------------------------------------------------------------------ #
# 0.  Helpers
# ------------------------------------------------------------------ #
HEADERS = {"User-Agent": "crypto-metrics-bot/1.0"}

def safe_get_json(url: str, timeout: int = 10):
    """Return parsed JSON or None (never raises)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, json.JSONDecodeError) as err:
        print(f"[WARN] {url} – {err}")
        return None

# ------------------------------------------------------------------ #
# 1.  Individual metric fetchers
# ------------------------------------------------------------------ #
def dev_contributors() -> int | None:
    """Monthly active OSS contributors (Electric Capital)."""
    csv_url = ("https://raw.githubusercontent.com/"
               "electric-capital/crypto-ecosystems/main/report_2024.csv")
    try:
        lines = requests.get(csv_url, headers=HEADERS, timeout=15).text.splitlines()
        last = lines[-1].split(",")
        return int(last[-1])
    except Exception as e:
        print(f"[WARN] dev_contributors – {e}")
        return None

def vc_stats() -> tuple[int | None, int | None]:
    """VC capital deployed ($M) and deal count (Galaxy Digital report)."""
    # 🔧 replace with real API when available
    return 3500, 416

def defi_tvl() -> float | None:
    """Total DeFi TVL (billions USD) – DefiLlama."""
    data = safe_get_json("https://api.llama.fi/summary/all")
    if data and "tvl" in data:
        return round(data["tvl"] / 1e9, 2)
    return None

def stablecoin_24h() -> float | None:
    """Stable-coin settlement (billions USD / 24 h)."""
    # 🔧 placeholder until you add a CoinMetrics key
    return 15.0

def etf_flow() -> float | None:
    """Spot BTC ETF net flow (millions USD / day)."""
    return 120.0

def btc_oi() -> float | None:
    """CME Bitcoin futures open interest (billions USD)."""
    return 19.8

def hashrate() -> float | None:
    """Bitcoin network hash-rate (EH/s)."""
    data = safe_get_json("https://api.bitinfocharts.com/v1/bitcoin/hashrate")
    if data and "hashrate" in data:
        return round(data["hashrate"] / 1e18, 1)
    return None

def nft_volume() -> float | None:
    """Aggregate NFT volume (millions USD / day)."""
    return 1000.0  # 🔧 placeholder

def fear_greed() -> int | None:
    data = safe_get_json("https://api.alternative.me/fng/?limit=1")
    if data:
        return int(data["data"][0]["value"])
    return None

def google_trend() -> int | None:
    try:
        from pytrends.request import TrendReq
        pt = TrendReq()
        pt.build_payload(["Bitcoin"])
        return int(pt.interest_over_time()["Bitcoin"][-1])
    except Exception as e:
        print(f"[WARN] google_trend – {e}")
        return None

# ------------------------------------------------------------------ #
# 2.  Build and push the Notion row
# ------------------------------------------------------------------ #
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB    = os.getenv("NOTION_DB")
if not (NOTION_TOKEN and NOTION_DB):
    raise RuntimeError("NOTION_TOKEN or NOTION_DB missing from env")

notion = Client(auth=NOTION_TOKEN)
today  = dt.date.today().isoformat()
vc_usd, vc_deals = vc_stats()

payload = {
    "parent": {"database_id": NOTION_DB},
    "properties": {
        "Date":                   {"date": {"start": today}},
        "Dev Contributors":       {"number": dev_contributors()},
        "VC $ Deployed ($M)":     {"number": vc_usd},
        "VC Deals":               {"number": vc_deals},
        "DeFi TVL ($B)":          {"number": defi_tvl()},
        "Stablecoin Settled ($B/24 h)": {"number": stablecoin_24h()},
        "ETF Net Flow ($M/day)":  {"number": etf_flow()},
        "BTC Hashrate (EH/s)":    {"number": hashrate()},
        "CME OI ($B)":            {"number": btc_oi()},
        "NFT Vol ($M/day)":       {"number": nft_volume()},
        "Fear-Greed":             {"number": fear_greed()},
        "Google Trend":           {"number": google_trend()},
    },
}

notion.pages.create(**payload)
print(f"Inserted metrics for {today}")
