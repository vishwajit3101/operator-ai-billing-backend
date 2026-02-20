# app/anthropic.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_ADMIN_KEY = os.getenv("ANTHROPIC_ADMIN_KEY")
ANTHROPIC_ORG_ID = os.getenv("ANTHROPIC_ORG_ID")

def get_anthropic_remaining_credits() -> float:
    """
    Fetch real remaining credits/balance from Anthropic Organization Billing API.
    Requires admin key (sk-ant-admin-...) and organization ID.
    Falls back to mock on error or missing config.
    """
    if not ANTHROPIC_ADMIN_KEY or not ANTHROPIC_ORG_ID:
        print("[Anthropic] Missing admin key or org ID → mock 42350")
        return 42350.0

    # Anthropic billing endpoint
    url = f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/billing/credits"
    headers = {
        "x-api-key": ANTHROPIC_ADMIN_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"[Anthropic] Status: {resp.status_code}")
        print(f"[Anthropic] Response preview: {resp.text[:300]}...")

        if resp.status_code == 401:
            print("[Anthropic] 401 Unauthorized - Check if you are using an Admin key (sk-ant-admin-...)")
            return 42350.0

        resp.raise_for_status()
        data = resp.json()

        remaining = data.get("credits_remaining", data.get("balance", data.get("remaining", 42350.0)))
        print(f"[Anthropic] Real remaining: {remaining}")
        return float(remaining)

    except Exception as e:
        print(f"[Anthropic] Error: {str(e)} → mock 42350")
        return 42350.0
