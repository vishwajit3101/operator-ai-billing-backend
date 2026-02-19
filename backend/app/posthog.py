# app/posthog.py
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY")
POSTHOG_PROJECT_ID = os.getenv("POSTHOG_PROJECT_ID")
POSTHOG_PERSONAL_API_KEY = os.getenv("POSTHOG_PERSONAL_API_KEY")


# Exact mapping from your PRD
EVENT_CREDIT_MAPPING = {
    "search_performed": ("Tavily", 1),
    "lead_enriched": ("FullEnrich", 2),
    "ai_workflow_run": ("Anthropic", 5),
    "data_fetched": ("Buyercaddy", 1),
}

def fetch_posthog_event_count(event_name: str, days: int = 7) -> int:
    """Count occurrences of an event in last N days using HogQL."""
    if not POSTHOG_API_KEY or not POSTHOG_PROJECT_ID:
        print(f"[PostHog] Missing config for '{event_name}'")
        return 0

    url = f"{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/query/"
    headers = {
        "Authorization": f"Bearer {POSTHOG_PERSONAL_API_KEY}",
        "Content-Type": "application/json"
    }

    query = f"""
    SELECT count() as cnt
    FROM events
    WHERE event = '{event_name}'
      AND timestamp >= now() - INTERVAL '{days} DAY'
    """

    payload = {"query": {"kind": "HogQLQuery", "query": query}}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        resp.raise_for_status()
        result = resp.json()
        count = result.get("results", [[0]])[0][0]
        print(f"[PostHog] {event_name} count (last {days}d): {count}")
        return int(count)
    except Exception as e:
        print(f"[PostHog] Error for {event_name}: {str(e)}")
        return 0


def get_real_daily_credit_usage(days: int = 7) -> dict[str, float]:
    """Calculate avg daily credit usage per tool from real PostHog events."""
    daily_usage = {}

    for event, (tool, credits_per) in EVENT_CREDIT_MAPPING.items():
        count = fetch_posthog_event_count(event, days)
        daily_credits = (count * credits_per) / days
        daily_usage[tool] = daily_usage.get(tool, 0.0) + daily_credits

    print(f"[PostHog] Real daily credit usage (last {days}d): {daily_usage}")
    return daily_usage