#!/usr/bin/env python3
"""Debug your NOTION_TOKEN / NOTION_DB setup."""

import os, json
from notion_client import Client

token = os.getenv("NOTION_TOKEN")
db_id  = os.getenv("NOTION_DB")

if not (token and db_id):
    raise SystemExit("⛔  NOTION_TOKEN or NOTION_DB missing from env")

client = Client(auth=token)

try:
    db = client.databases.retrieve(database_id=db_id)
except Exception as e:
    print("❌  Could NOT retrieve the database:", e)
    raise SystemExit(1)

print("✅  Database found!\n")
print("🔑  Properties visible to the API:")
for key in db["properties"]:
    print("   •", repr(key))
