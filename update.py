#!/usr/bin/env python3
"""
Push daily crypto-market proxy metrics into a Notion database.

Env variables required:
  NOTION_TOKEN  – the Internal Integration Secret (secret_xxx or ntn_xxx)
  NOTION_DB     – 32-char database ID of your Notion table
"""

import os
import datetime as dt
import requests
from notion_client import Client

# --------------------------------------------------------------------- #
# 1.  Set up Notion client
# --------------------------------------------------------------------- #
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB    = os.getenv("NOTION_DB")

if not (NOTION_TOKEN and NOTION_DB):
    raise RuntimeError("Missing NOTION_TOKEN or NOTION_DB environment vars")

notion = Client(auth=NOTION_TOKEN)
today  = dt.date.today().isoformat()

# --------------------------------------------------------------------- #
# 2.  Helper functions for each metric
#     Replace placeholders with live API calls as you add keys.
# --------------------------------------------------------------------- #
def dev_contributors() -> int:
    """Monthly active OSS contributors – Electric Capital Developer Report CSV"""
    csv_url = "https://raw.githubusercontent.com/electric-capital/crypto-ecosystems/main/report_2024.csv"
    try:
        df = requests.get(csv_url, timeout=15).text.splitlines()
        # Very simplified parse: last line = latest total dev count
        last_line = df[-1].split(",")
        return int(last_line[-1])
    except Exception:
        return None   # gracefully handle failures

def vc_stats() -> tuple[int, int]:
    """VC capital deployed ($M) + deal count – Galaxy Digital report JSON"""
    # Replace with real endpoint once published
    return 3500, 416               # $3.5 B, 416 deals

def defi_tvl() -> float:
    """Total DeFi TVL – DefiLlama (billions USD)"""
    data = requests.get("https://api.llama.fi/tvl", timeout=10).json()
    return round(data["tvl"] / 1e9, 2)

def stablecoin_24h() -> float:
    """Stable-coin settlement – CoinMetrics or The Block (billions USD / 24 h)"""
    # Placeholder until you add API key
    return 15.0

def etf_flow() -> float:
    """Spot Bitcoin ETF net flow – The Block ETF dashboard (millions USD / day)"""
    return 120.0

def btc_oi() -> float:
    """CME Bitcoin futures open interest (billions USD)"""
    return 19.8

def hashrate() -> float:
    """Bitcoin network hash-rate (EH/s) – BitInfoCharts API"""
    url = "https://api.bitinfocharts.com/v1/bitcoin/hashrate"
    data = requests.get(url, timeout=10).json()
    return round(data["hashrate"] / 1e18, 1)

def nft_volume() -> float:
    """Aggregate NFT volume (millions USD / day) – CryptoSlam placeholder"""
    return 1000.0

def fear_greed() -> int:
    """Crypto Fear & Greed Index (0-100) – Alternative.me"""
    url = "https://api.alternative.me/fng/?limit=1"
    data = requests.get(url, timeout=10).json()
    return int(data["data"][0]["value"])

def google_trend() -> int:
    """Google Trends score for 'Bitcoin' – via pytrends"""
    try:
        from pytrends.request import TrendReq
        pytrend = TrendReq()
        pytrend.build_payload(["Bitcoin"])
        return int(pytrend.interest_over_time()["Bitcoin"][-1])
    except Exception:
        return None

# --------------------------------------------------------------------- #
# 3.  Build the Notion payload
# --------------------------------------------------------------------- #
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
        "Google Trend":           {"number": google_trend()}}
   
