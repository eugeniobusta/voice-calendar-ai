#!/usr/bin/env python3
"""
setup_telegram_webhook.py — Run this ONCE after deploying to Render.

WHAT IS A WEBHOOK?
  Normally to receive messages, you'd have to constantly ask Telegram
  "hey, any new messages?" (called polling). That wastes resources.

  A webhook is the opposite: you tell Telegram "when someone messages
  my bot, POST it to THIS URL". Telegram does the work, you just wait.

  This script registers your Render URL as the webhook.
  You only need to run it once — it persists until you change it.

BEFORE RUNNING:
  1. Add TELEGRAM_BOT_TOKEN to your .env
  2. Add RENDER_URL to your .env (e.g. https://voice-calendar-ai.onrender.com)
  3. Make sure you've pushed and deployed to Render
  4. Run: python setup_telegram_webhook.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token      = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
render_url = os.getenv("RENDER_URL", "").strip()

if not token:
    print("\n  ERROR: TELEGRAM_BOT_TOKEN not set in .env")
    print("  Get it from @BotFather on Telegram\n")
    exit(1)

if not render_url:
    print("\n  ERROR: RENDER_URL not set in .env")
    print("  Example: RENDER_URL=https://voice-calendar-ai.onrender.com\n")
    exit(1)

webhook_url = f"{render_url.rstrip('/')}/telegram"

print(f"  Setting webhook to: {webhook_url}")

response = requests.post(
    f"https://api.telegram.org/bot{token}/setWebhook",
    json={"url": webhook_url},
    timeout=10,
)
result = response.json()

if result.get("ok"):
    print(f"  ✓ Done! Telegram will now POST all messages to your server.")
    print(f"\n  Next: open Telegram, find your bot, and send /start")
    print(f"  It will reply with your chat ID — add that as TELEGRAM_CHAT_ID\n")
else:
    print(f"  ✗ Failed: {result}\n")
