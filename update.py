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

def defi_tvl() -> float | None:
    """Total DeFi TVL (billions USD) – DefiLlama."""
    data = safe_get_json("https://yields.llama.fi/tvl")
    if data and "tvl" in data:
        return round(data["tvl"] / 1e9, 2)
    return None

def stablecoin_24h() -> float | None:
    url = "https://stablecoins.llama.fi/summary?adjusted=true&span=24h"
    d = safe_get_json(url)
    try:
        return round(d["flow"]["24h"] / 1e9, 1)   # returns raw USD
    except (TypeError, KeyError):
        return None

def etf_flow() -> float | None:
    url = "https://raw.githubusercontent.com/absoluteblast/etf-flows/main/latest.json"
    d = safe_get_json(url)
    try:
        return round(d["netflow_m"], 1)
    except (TypeError, KeyError):
        return None

def btc_oi() -> float | None:
    url = "https://api.blockchaincenter.net/cme/openinterest"
    d = safe_get_json(url)
    try:
        return round(d["open_interest_usd"] / 1e9, 2)
    except (TypeError, KeyError):
        return None

def hashrate() -> float | None:
    try:
        phs = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        return round(phs / 1e6, 1)   # convert PH/s → EH/s
    except Exception as e:
        print("[WARN] hashrate –", e)
        return None

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

def meme_volume_m() -> float | None:
    """Sum 24‑h volume of all coins in CoinGecko's 'meme‑token' category."""
    total = 0
    try:
        for page in (1, 2):          # first 500 tokens
            url = (f"https://api.coingecko.com/api/v3/coins/markets"
                   f"?vs_currency=usd&category=meme-token"
                   f"&order=volume_desc&per_page=250&page={page}&sparkline=false")
            data = requests.get(url, timeout=15).json()
            if not data:
                break
            total += sum(c["total_volume"] for c in data if c["total_volume"])
    except Exception as e:
        print("[WARN] meme_volume –", e)
        return None
    return round(total / 1e6, 1)        # to millions USD

# ------------------------------------------------------------------ #
# 2.  Build and push the Notion row
# ------------------------------------------------------------------ #
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB    = os.getenv("NOTION_DB")
if not (NOTION_TOKEN and NOTION_DB):
    raise RuntimeError("NOTION_TOKEN or NOTION_DB missing from env")

notion = Client(auth=NOTION_TOKEN)
today  = dt.date.today().isoformat()

payload = {
    "parent": {"database_id": NOTION_DB},
    "properties": {
        "Date":                   {"date": {"start": today}},
        "Stablecoin Settled ($B/24 h)": {"number": stablecoin_24h()},
        "ETF Net Flow ($M/day)":  {"number": etf_flow()},
        "BTC Hashrate (EH/s)":    {"number": hashrate()},
        "CME OI ($B)":            {"number": btc_oi()},
        "Fear-Greed":             {"number": fear_greed()},
        "Google Trend":           {"number": google_trend()},
        "Meme Volume M":          {"number": meme_volume_m()},
    },
}

notion.pages.create(**payload)
print(f"Inserted metrics for {today}")
