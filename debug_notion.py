#!/usr/bin/env python3
"""Quick sanity-check for NOTION_TOKEN + NOTION_DB secrets.

It prints:
  • whether the API can reach the database
  • the property names the API sees
"""

import os, json
from notion_client import Client

token = os.getenv("NOTION_TOKEN")
db_id  = os.getenv("NOTION_DB")

if not (token and db_id):
    raise SystemExit("⛔  NOTION_TOKEN or NOTION_DB not in env")

client = Client(auth=token)

try:
    db = client.databases.retrieve(db_id=db_id)
except Exception as e:
    print("❌  Could NOT retrieve the database:", e)
    raise SystemExit(1)

print("✅  Database found!\n")
print("🔑  Property keys visible to the API:")
for name in db["properties"]:
    print("   •", repr(name))
