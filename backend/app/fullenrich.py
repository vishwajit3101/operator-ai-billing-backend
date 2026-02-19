# app/fullenrich.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

FULLENRICH_API_KEY = os.getenv("FULLENRICH_API_KEY")
FULLENRICH_USAGE_URL = os.getenv("FULLENRICH_USAGE_URL", "https://api.fullenrich.com/v1/usage")  # ← mentor must confirm this URL

def get_fullenrich_remaining_credits() -> float:
    if not FULLENRICH_API_KEY:
        print("[FullEnrich] No API key in .env → using mock 500")
        return 500.0

    headers = {"Authorization": f"Bearer {FULLENRICH_API_KEY}"}

    try:
        resp = requests.get(FULLENRICH_USAGE_URL, headers=headers, timeout=8)
        print(f"[FullEnrich] Status code: {resp.status_code}")
        print(f"[FullEnrich] Response preview: {resp.text[:300]}...")

        resp.raise_for_status()
        data = resp.json()

        # Adjust key based on actual response (mentor may need to tell you the correct field)
        remaining = data.get("credits_remaining", data.get("balance", data.get("remaining", 500.0)))
        print(f"[FullEnrich] Real remaining: {remaining}")
        return float(remaining)

    except Exception as e:
        print(f"[FullEnrich] Error: {str(e)} → using mock 500")
        return 500.0