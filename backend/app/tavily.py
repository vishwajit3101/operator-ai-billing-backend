import requests
import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def get_tavily_remaining_credits() -> float:
    if not TAVILY_API_KEY:
        print("[Tavily] No API key in .env → fallback to mock 2800")
        return 2800.0

    url = "https://api.tavily.com/usage"
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}"}

    try:
        resp = requests.get(url, headers=headers, timeout=8)
        print(f"[Tavily] Status code: {resp.status_code}")
        print(f"[Tavily] Response preview: {resp.text[:300]}...")

        resp.raise_for_status()
        data = resp.json()

        # From your actual response: limit is in account.plan_limit, usage is in key.usage
        plan_limit = data.get("account", {}).get("plan_limit", 1000)
        total_usage = data.get("key", {}).get("usage", 0)
        remaining = plan_limit - total_usage

        print(f"[Tavily] Real remaining (limit - usage): {remaining}")
        return float(remaining)

    except Exception as e:
        print(f"[Tavily] Error: {str(e)} → fallback to mock 2800")
        return 2800.0